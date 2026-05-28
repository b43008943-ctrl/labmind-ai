/* ═══════════════════════════════════════════════════════════════════════════════
   LabMind AI — عميل الـ API المركزي
   ═══════════════════════════════════════════════════════════════════════════════
   جميع طلبات الخادم تمر عبر هذا الملف.
   يتم تخزين رمز JWT في localStorage وإرفاقه بكل طلب.

   الاستخدام:
   ─────────
   import { api } from '@/services/apiClient'

   // تسجيل الدخول
   await api.auth.login('user@example.com', 'password')

   // تحليل صورة الطفيليات
   const result = await api.parasitology.analyzeAnnotated(imageFile)

   // الحصول على التقرير السريري
   const report = await api.parasitology.clinicalReport(result.detections)
   ═══════════════════════════════════════════════════════════════════════════════ */

// Auto-detect: on mobile (192.168.x.x), use the same host as the page.
// On localhost, use localhost. Env vars override if explicitly set.
// On Cloudflare tunnels, use the build-time VITE_API_BASE_URL.
function _resolveApiBase() {
  const hostname = window.location.hostname

  // Localhost
  if (hostname === 'localhost' || hostname === '127.0.0.1') {
    return 'http://localhost:8000'
  }

  // Local network (WiFi)
  if (hostname.startsWith('192.168.') || 
      hostname.startsWith('10.') || 
      hostname.startsWith('172.')) {
    return `http://${hostname}:8000`
  }

  // Cloudflare tunnel — use hardcoded backend tunnel URL
  // This gets updated by the tunnel renewal script
  const CLOUDFLARE_BACKEND = 'https://deposits-varieties-brought-syndication.trycloudflare.com'
  return CLOUDFLARE_BACKEND
}
export const API_BASE_URL = _resolveApiBase();

// ═══════════════════════════════════════════════════════════════════════════════
// إدارة الرمز المميز (Token)
// ═══════════════════════════════════════════════════════════════════════════════

const TOKEN_KEY = 'labmind_auth_token';

export const tokenStore = {
  /** الحصول على الرمز المميز من التخزين المحلي */
  get() {
    try {
      return localStorage.getItem(TOKEN_KEY);
    } catch {
      // التصفح الخاص قد يمنع الوصول إلى localStorage
      return null;
    }
  },

  /** حفظ الرمز المميز في التخزين المحلي */
  set(token) {
    try {
      localStorage.setItem(TOKEN_KEY, token);
    } catch {
      // تجاهل — التصفح الخاص
    }
  },

  /** مسح الرمز المميز من التخزين المحلي */
  clear() {
    try {
      localStorage.removeItem(TOKEN_KEY);
    } catch {
      // تجاهل — التصفح الخاص
    }
  },
};

// ═══════════════════════════════════════════════════════════════════════════════
// فئة الأخطاء المخصصة
// ═══════════════════════════════════════════════════════════════════════════════

export class ApiError extends Error {
  /**
   * @param {string} message — رسالة الخطأ
   * @param {number} status  — رمز حالة HTTP
   * @param {*}      payload — بيانات الاستجابة الأصلية
   */
  constructor(message, status, payload) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.payload = payload;
  }
}

// ═══════════════════════════════════════════════════════════════════════════════
// دالة الطلب الأساسية — جوهر جميع الاتصالات
// ═══════════════════════════════════════════════════════════════════════════════

/**
 * @param {string} path — المسار النسبي (مثلاً '/api/auth/me')
 * @param {object} options
 * @param {string}  [options.method='GET']
 * @param {*}       [options.body]           — الجسم: كائن JSON أو FormData أو سلسلة
 * @param {object}  [options.query]          — معلمات الاستعلام
 * @param {boolean} [options.requireAuth=true]
 * @param {boolean} [options.isFormData=false]
 * @param {boolean} [options.isFormUrlEncoded=false]
 * @param {AbortSignal} [options.signal]
 * @returns {Promise<any>}
 */
export async function request(path, options = {}) {
  const {
    method = 'GET',
    body,
    query,
    requireAuth = true,
    isFormData = false,
    isFormUrlEncoded = false,
    signal,
  } = options;

  // ── بناء الترويسات ──
  const headers = {};

  if (requireAuth) {
    const token = tokenStore.get();
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }
  }

  if (body && !isFormData) {
    if (isFormUrlEncoded) {
      headers['Content-Type'] = 'application/x-www-form-urlencoded';
    } else {
      headers['Content-Type'] = 'application/json';
    }
  }
  // لا نضع Content-Type في حالة FormData — المتصفح يضيفه تلقائياً مع boundary

  // ── بناء سلسلة الاستعلام ──
  let url = `${API_BASE_URL}${path}`;
  if (query && typeof query === 'object') {
    const params = new URLSearchParams();
    for (const [key, value] of Object.entries(query)) {
      if (value !== null && value !== undefined && value !== '') {
        params.set(key, String(value));
      }
    }
    const qs = params.toString();
    if (qs) url += `?${qs}`;
  }

  // ── تنفيذ الطلب ──
  let response;
  try {
    response = await fetch(url, {
      method,
      headers,
      body: body ?? undefined,
      signal,
    });
  } catch (networkError) {
    // خطأ في الشبكة — الخادم لا يعمل أو لا يمكن الوصول إليه
    throw new ApiError(
      `تعذر الاتصال بالخادم على ${API_BASE_URL}. تأكد من أن الخادم يعمل على المنفذ 8000.`,
      0,
      { originalError: networkError.message },
    );
  }

  // ── التعامل مع 401 — انتهاء الجلسة ──
  if (response.status === 401) {
    tokenStore.clear();
    // إرسال حدث مخصص لتنبيه التطبيق بانتهاء الجلسة
    window.dispatchEvent(new CustomEvent('auth:unauthorized'));
    throw new ApiError(
      'انتهت صلاحية الجلسة. يرجى تسجيل الدخول مرة أخرى.',
      401,
    );
  }

  // ── قراءة الاستجابة ──
  let data = null;
  const contentType = response.headers.get('content-type') || '';
  if (contentType.includes('application/json')) {
    data = await response.json();
  } else {
    const text = await response.text();
    if (text) data = text;
  }

  // ── التعامل مع الأخطاء الأخرى ──
  if (!response.ok) {
    const message =
      data?.detail || data?.message || `فشل الطلب (${response.status})`;
    throw new ApiError(message, response.status, data);
  }

  return data;
}

// ═══════════════════════════════════════════════════════════════════════════════
// دوال مساعدة داخلية
// ═══════════════════════════════════════════════════════════════════════════════

/** بناء FormData من ملف — اسم الحقل دائماً "file" */
function _fileForm(file) {
  const fd = new FormData();
  fd.append('file', file);
  return fd;
}

/** ترميز معرّف المسار لمنع مشاكل الحقن */
const _enc = (id) => encodeURIComponent(id);

// ═══════════════════════════════════════════════════════════════════════════════
//  1. المصادقة — auth
// ═══════════════════════════════════════════════════════════════════════════════

const auth = {
  /** تسجيل حساب جديد — لا يحتاج مصادقة */
  register(userData) {
    return request('/api/auth/register', {
      method: 'POST',
      body: JSON.stringify(userData),
      requireAuth: false,
    });
  },

  /** تسجيل الدخول — يرسل بيانات form-urlencoded ويحفظ الرمز تلقائياً */
  async login(username, password) {
    const data = await request('/api/auth/token', {
      method: 'POST',
      body: JSON.stringify({ email: username, password }),
      requireAuth: false,
    });
    if (data?.access_token) {
      tokenStore.set(data.access_token);
    }
    return data;
  },

  /** تسجيل الخروج — محلي فقط، لا يوجد طلب للخادم */
  logout() {
    tokenStore.clear();
  },

  /** جلب بيانات المستخدم الحالي */
  getCurrentUser() {
    return request('/api/auth/me');
  },

  /** تحديث الملف الشخصي */
  updateProfile(profileData) {
    return request('/api/auth/profile', {
      method: 'PUT',
      body: JSON.stringify(profileData),
    });
  },

  /** هل المستخدم مسجّل الدخول؟ */
  isAuthenticated() {
    return !!tokenStore.get();
  },

  /** تغيير كلمة المرور */
  changePassword(data) {
    return request('/api/auth/change-password', {
      method: 'PUT',
      body: JSON.stringify(data),
    });
  },

  /** حذف الحساب نهائياً */
  deleteAccount() {
    return request('/api/auth/account', {
      method: 'DELETE',
    });
  },
};

// ═══════════════════════════════════════════════════════════════════════════════
//  2. أمراض الدم — hematology
// ═══════════════════════════════════════════════════════════════════════════════

const hematology = {
  /** إنشاء تقرير سريري من بيانات التحليل */
  clinicalReport(analysisData) {
    return request('/api/hematology/clinical-report', {
      method: 'POST',
      body: JSON.stringify(analysisData),
    });
  },
};

// ═══════════════════════════════════════════════════════════════════════════════
//  بناء مساحة أسماء لمختبرات التشخيص المجهري
//  (نمط موحد: urinalysis / parasitology / microbiology)
// ═══════════════════════════════════════════════════════════════════════════════

function _buildMicroscopyLab(prefix) {
  return {
    /** تحليل صورة (بدون تأشير) */
    analyze(file) {
      return request(`${prefix}/analyze`, {
        method: 'POST',
        body: _fileForm(file),
        isFormData: true,
      });
    },

    /** تحليل صورة مع إعادة الصورة المؤشّرة */
    analyzeAnnotated(file, options = {}) {
      const fd = _fileForm(file);
      if (options.confidence != null) {
        fd.append('confidence', String(options.confidence));
      }
      return request(`${prefix}/analyze-annotated`, {
        method: 'POST',
        body: fd,
        isFormData: true,
      });
    },

    /** معلومات النموذج */
    getModelInfo() {
      return request(`${prefix}/model-info`);
    },

    /** إعادة تحميل النموذج */
    reloadModel() {
      return request(`${prefix}/reload-model`, { method: 'POST' });
    },

    /** إنشاء تقرير سريري */
    clinicalReport(analysisData) {
      return request(`${prefix}/clinical-report`, {
        method: 'POST',
        body: JSON.stringify(analysisData),
      });
    },
  };
}

// ═══════════════════════════════════════════════════════════════════════════════
//  3. تحليل البول — urinalysis
// ═══════════════════════════════════════════════════════════════════════════════

const urinalysis = _buildMicroscopyLab('/api/urinalysis');

// ═══════════════════════════════════════════════════════════════════════════════
//  4. الطفيليات — parasitology
// ═══════════════════════════════════════════════════════════════════════════════

const parasitology = _buildMicroscopyLab('/api/parasitology');

// ═══════════════════════════════════════════════════════════════════════════════
//  5. الأحياء الدقيقة — microbiology
// ═══════════════════════════════════════════════════════════════════════════════

const microbiology = _buildMicroscopyLab('/api/microbiology');

// ═══════════════════════════════════════════════════════════════════════════════
//  6. الذكاء الاصطناعي / رشا — ai
// ═══════════════════════════════════════════════════════════════════════════════

const ai = {
  /** محادثة رشا — المساعد الذكي */
  askRasha(payload) {
    return request('/api/ai/ask-rasha', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  /** قائمة جلسات المحادثة */
  listSessions() {
    return request('/api/ai/sessions');
  },

  /** رسائل جلسة محددة */
  getSessionMessages(sessionId) {
    return request(`/api/ai/sessions/${_enc(sessionId)}/messages`);
  },

  /** توليد اختبار (كويز) بموضوع محدد */
  generateQuiz(payload) {
    return request('/api/ai/generate-quiz', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  /** توليد اختبار ذكي من نص */
  generateSmartQuiz(payload) {
    return request('/api/ai/generate-smart-quiz', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  /** تلخيص نص */
  summarize(payload) {
    return request('/api/ai/summarize', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  /** توليد سيناريو فيديو تعليمي */
  generateVideoScript(payload) {
    return request('/api/ai/generate-video-script', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  /** توليد صورة هولوغرافية */
  generateHoloImage(payload) {
    return request('/api/ai/generate-holo-image', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },
};

// ═══════════════════════════════════════════════════════════════════════════════
//  7. محلل نتائج التحاليل — labResults
// ═══════════════════════════════════════════════════════════════════════════════

const labResults = {
  /** تحليل ملف نتائج مخبرية (PDF / صورة) */
  analyze(file) {
    return request('/api/lab-results/analyze', {
      method: 'POST',
      body: _fileForm(file),
      isFormData: true,
    });
  },
};

// ═══════════════════════════════════════════════════════════════════════════════
//  8. مولّد الفيديو التعليمي — videoGenerator
// ═══════════════════════════════════════════════════════════════════════════════

const videoGenerator = {
  /** رفع ملف وتوليد عرض شرائح تعليمي */
  generate(file) {
    return request('/api/video-generator/generate', {
      method: 'POST',
      body: _fileForm(file),
      isFormData: true,
    });
  },
};

// ═══════════════════════════════════════════════════════════════════════════════
//  9. المرضى — patients
// ═══════════════════════════════════════════════════════════════════════════════

const patients = {
  /** إنشاء سجل مريض جديد */
  create(data) {
    return request('/api/patients/', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  /** قائمة المرضى مع تصفية */
  list({ skip = 0, limit = 50, search = '' } = {}) {
    return request('/api/patients/', { query: { skip, limit, search } });
  },

  /** بيانات مريض واحد */
  get(patientId) {
    return request(`/api/patients/${_enc(patientId)}`);
  },

  /** تحديث بيانات مريض */
  update(patientId, updates) {
    return request(`/api/patients/${_enc(patientId)}`, {
      method: 'PATCH',
      body: JSON.stringify(updates),
    });
  },
};

// ═══════════════════════════════════════════════════════════════════════════════
//  10. الحالات المخبرية — cases
// ═══════════════════════════════════════════════════════════════════════════════

const cases = {
  /** إنشاء حالة مخبرية جديدة */
  create(data) {
    return request('/api/cases/', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  /** قائمة الحالات مع تصفية */
  list({ skip = 0, limit = 50, status = '', department = '' } = {}) {
    return request('/api/cases/', { query: { skip, limit, status, department } });
  },

  /** بيانات حالة واحدة */
  get(caseId) {
    return request(`/api/cases/${_enc(caseId)}`);
  },

  /** تحديث حالة الحالة */
  updateStatus(caseId, statusData) {
    return request(`/api/cases/${_enc(caseId)}/status`, {
      method: 'PATCH',
      body: JSON.stringify(statusData),
    });
  },

  /** رفع ملف أصل (صورة شريحة مثلاً) */
  uploadAsset(caseId, file) {
    return request(`/api/cases/${_enc(caseId)}/assets`, {
      method: 'POST',
      body: _fileForm(file),
      isFormData: true,
    });
  },

  /** قائمة أصول حالة */
  listAssets(caseId) {
    return request(`/api/cases/${_enc(caseId)}/assets`);
  },
};

// ═══════════════════════════════════════════════════════════════════════════════
//  11. الأصول — assets
// ═══════════════════════════════════════════════════════════════════════════════

const assets = {
  /** تحميل ملف أصل */
  download(assetId) {
    return request(`/api/assets/${_enc(assetId)}/download`);
  },

  /** حذف أصل */
  delete(assetId) {
    return request(`/api/assets/${_enc(assetId)}`, { method: 'DELETE' });
  },
};

// ═══════════════════════════════════════════════════════════════════════════════
//  12. التحليلات القديمة (V1) — analyses
// ═══════════════════════════════════════════════════════════════════════════════

const analyses = {
  /** بدء تحليل لحالة/أصل */
  trigger(payload) {
    return request('/api/analyses/trigger', {
      method: 'POST',
      body: JSON.stringify(payload),
    });
  },

  /** حالة تشغيل التحليل */
  getStatus(runId) {
    return request(`/api/analyses/runs/${_enc(runId)}`);
  },

  /** قائمة تحليلات حالة */
  listByCase(caseId) {
    return request(`/api/analyses/cases/${_enc(caseId)}`);
  },

  /** الصورة المؤشّرة لتحليل */
  getAnnotatedImage(runId) {
    return request(`/api/analyses/runs/${_enc(runId)}/annotated-image`);
  },
};

// ═══════════════════════════════════════════════════════════════════════════════
//  13. التقارير — reports
// ═══════════════════════════════════════════════════════════════════════════════

const reports = {
  /** إنشاء تقرير جديد */
  create(data) {
    return request('/api/reports/', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  },

  /** قائمة جميع التقارير مع تصفية */
  list({ case_id = '', status = '', skip = 0, limit = 50 } = {}) {
    return request('/api/reports/', {
      query: { case_id, status, skip, limit },
    });
  },

  /** تقاريري */
  listMyReports({ skip = 0, limit = 50 } = {}) {
    return request('/api/reports/my-reports', { query: { skip, limit } });
  },

  /** الأرشيف */
  listMyArchive() {
    return request('/api/reports/my-archive');
  },

  /** التقارير المعلّقة للمراجعة */
  listPendingReviews({ skip = 0, limit = 50 } = {}) {
    return request('/api/reports/pending-review', { query: { skip, limit } });
  },

  /** تقرير واحد */
  get(reportId) {
    return request(`/api/reports/${_enc(reportId)}`);
  },

  /** تحديث تقرير */
  update(reportId, updates) {
    return request(`/api/reports/${_enc(reportId)}`, {
      method: 'PATCH',
      body: JSON.stringify(updates),
    });
  },

  /** إرسال للمراجعة */
  submitForReview(reportId) {
    return request(`/api/reports/${_enc(reportId)}/submit`, { method: 'POST' });
  },

  /** مراجعة تقرير */
  review(reportId, reviewData) {
    return request(`/api/reports/${_enc(reportId)}/review`, {
      method: 'POST',
      body: JSON.stringify(reviewData),
    });
  },

  /** أرشفة تقرير */
  archive(reportId) {
    return request(`/api/reports/${_enc(reportId)}/archive`, { method: 'POST' });
  },
};

// ═══════════════════════════════════════════════════════════════════════════════
//  14. التنبيهات — alerts
// ═══════════════════════════════════════════════════════════════════════════════

const alerts = {
  /** قائمة التنبيهات */
  list({ include_dismissed = false } = {}) {
    return request('/api/alerts/', {
      query: { include_dismissed: include_dismissed ? 'true' : '' },
    });
  },

  /** عدد التنبيهات غير المقروءة */
  unreadCount() {
    return request('/api/alerts/unread-count');
  },

  /** تعيين تنبيه كمقروء */
  markRead(alertId) {
    return request(`/api/alerts/${_enc(alertId)}/read`, { method: 'POST' });
  },

  /** إخفاء تنبيه */
  dismiss(alertId) {
    return request(`/api/alerts/${_enc(alertId)}/dismiss`, { method: 'POST' });
  },
};

// ═══════════════════════════════════════════════════════════════════════════════
//  15. فحص صحة الخادم — health
// ═══════════════════════════════════════════════════════════════════════════════

const health = {
  /** فحص سريع — لا يحتاج مصادقة */
  check() {
    return request('/health', { requireAuth: false });
  },
};

// ═══════════════════════════════════════════════════════════════════════════════
//  الكائن الرئيسي — يجمع كل مساحات الأسماء
// ═══════════════════════════════════════════════════════════════════════════════

export const api = {
  auth,
  hematology,
  urinalysis,
  parasitology,
  microbiology,
  ai,
  labResults,
  videoGenerator,
  patients,
  cases,
  assets,
  analyses,
  reports,
  alerts,
  health,
};

export default api;

// ═══════════════════════════════════════════════════════════════════════════════
//  تصديرات التوافق مع الإصدار السابق (V1)
//  ─────────────────────────────────────────
//  الملفات القديمة تستورد دوال منفردة مثل:
//    import { login, askRasha, listAlerts } from '../services/apiClient'
//  هذه التصديرات تحافظ على التوافق حتى يتم تحديث جميع الملفات.
// ═══════════════════════════════════════════════════════════════════════════════

// ── Auth ──
export const login = auth.login.bind(auth);
export const register = auth.register.bind(auth);
export const fetchCurrentUser = auth.getCurrentUser.bind(auth);
export const updateUserProfile = auth.updateProfile.bind(auth);

// ── Token (دوال مباشرة للتوافق) ──
export function getToken() { return tokenStore.get(); }
export function setToken(t) { tokenStore.set(t); }
export function clearToken() { tokenStore.clear(); }

// ── AI ──
export const askRasha = ai.askRasha.bind(ai);
export const generateQuiz = ai.generateQuiz.bind(ai);
export const summarizeText = (text) => ai.summarize({ text });

// ── Patients ──
export const createPatient = patients.create.bind(patients);
export const listPatients = patients.list.bind(patients);
export const getPatient = patients.get.bind(patients);
export const updatePatient = patients.update.bind(patients);

// ── Cases ──
export const createCase = cases.create.bind(cases);
export const listCases = cases.list.bind(cases);
export const getCase = cases.get.bind(cases);
export const updateCaseStatus = cases.updateStatus.bind(cases);

// ── Assets ──
export const uploadAsset = (caseId, file) => cases.uploadAsset(caseId, file);
export const listAssets = cases.listAssets.bind(cases);
export const downloadAsset = assets.download.bind(assets);
export const deleteAsset = assets.delete.bind(assets);

// ── Analyses (Legacy V1) ──
export const triggerAnalysis = analyses.trigger.bind(analyses);
export const getAnalysisStatus = analyses.getStatus.bind(analyses);
export const listCaseAnalyses = analyses.listByCase.bind(analyses);
export const getAnnotatedImage = analyses.getAnnotatedImage.bind(analyses);

// ── Reports ──
export const createReport = reports.create.bind(reports);
export const listMyReports = reports.listMyReports.bind(reports);
export const listMyArchive = reports.listMyArchive.bind(reports);
export const getReport = reports.get.bind(reports);
export const updateReport = reports.update.bind(reports);
export const submitForReview = reports.submitForReview.bind(reports);
export const archiveReport = reports.archive.bind(reports);

// ── Alerts ──
export const listAlerts = (includeDismissed = false) =>
  alerts.list({ include_dismissed: includeDismissed });
export const getUnreadAlertCount = alerts.unreadCount.bind(alerts);
export const markAlertRead = alerts.markRead.bind(alerts);
export const dismissAlert = alerts.dismiss.bind(alerts);
