/* ═══════════════════════════════════════════════════════════════
   STUDENT COMMUNITY — Realistic Educational Data
   ═══════════════════════════════════════════════════════════════ */

export const TRENDING_TOPICS = [
  { id:1, tag:'Parasitology', posts:234, trend:'↑', color:'#10B981' },
  { id:2, tag:'Hematology', posts:189, trend:'↑', color:'#EF4444' },
  { id:3, tag:'Microbiology', posts:156, trend:'↑', color:'#8B5CF6' },
  { id:4, tag:'Urinalysis', posts:134, trend:'→', color:'#F59E0B' },
  { id:5, tag:'SickleCell', posts:98, trend:'↑', color:'#EC4899' },
  { id:6, tag:'GramStain', posts:87, trend:'↑', color:'#3B82F6' },
  { id:7, tag:'Fasciolopsis', posts:76, trend:'↑', color:'#10B981' },
  { id:8, tag:'CBC_Analysis', posts:65, trend:'→', color:'#EF4444' },
];

export const INITIAL_STUDY_GROUPS = [
  { id:'g1', name:'Dragon Syndicate', members:245, online:12, subject:'parasitology', icon:'🐉', private:false, code:'DRAG01', description:'Elite parasitology research team' },
  { id:'g2', name:'Celestial Empire', members:189, online:8, subject:'hematology', icon:'⭐', private:false, code:'CELE02', description:'Blood cell analysis masters' },
  { id:'g3', name:'Mystic Mermaid', members:134, online:6, subject:'microbiology', icon:'🧜', private:true, code:'MYST03', description:'Gram stain classification experts' },
  { id:'g4', name:'Toxic Beast Clan', members:98, online:4, subject:'urinalysis', icon:'⚡', private:false, code:'TOXIC4', description:'Urine sediment analysis squad' },
  { id:'g5', name:'Cyber Mecha', members:210, online:15, subject:'clinical', icon:'🤖', private:false, code:'MECH05', description:'Clinical diagnosis technology team' },
  { id:'g6', name:'Astral Unicorns', members:76, online:3, subject:'ai', icon:'🦄', private:true, code:'ASTR06', description:'AI model training specialists' },
  { id:'g7', name:'Phoenix Rising', members:312, online:22, subject:'general', icon:'🔥', private:false, code:'PHNX07', description:'General medical science community' },
  { id:'g8', name:'Shadow Wolves', members:167, online:9, subject:'general', icon:'🐺', private:false, code:'WOLF08', description:'Competitive lab champions 2026' },
];

export const MOCK_LEADERBOARD = [
  { id:1, rank:1, name:'Ahmed Al-Rashidi', xp:4850, level:18, badge:'🥇', faculty:'Parasitology', wins:42, accuracy:'97%', color:'#FFD700', group:'Dragon Syndicate' },
  { id:2, rank:2, name:'Sara Mohammed', xp:4320, level:16, badge:'🥈', faculty:'Hematology', wins:38, accuracy:'95%', color:'#C0C0C0', group:'Celestial Empire' },
  { id:3, rank:3, name:'Omar Khalil', xp:3980, level:15, badge:'🥉', faculty:'Microbiology', wins:31, accuracy:'93%', color:'#CD7F32', group:'Mystic Mermaid' },
  { id:4, rank:4, name:'Fatima Al-Zahra', xp:3650, level:14, badge:'⭐', faculty:'Clinical Lab', wins:28, accuracy:'91%', color:'#8B5CF6', group:'Cyber Mecha' },
  { id:5, rank:5, name:'Ali Hassan', xp:3210, level:13, badge:'⭐', faculty:'Parasitology', wins:24, accuracy:'89%', color:'#3B82F6', group:'Dragon Syndicate' },
  { id:6, rank:6, name:'Nour Ibrahim', xp:2980, level:12, badge:'⭐', faculty:'Urinalysis', wins:21, accuracy:'88%', color:'#10B981', group:'Toxic Beast Clan' },
  { id:7, rank:7, name:'Youssef Ahmad', xp:2750, level:11, badge:'⭐', faculty:'Hematology', wins:19, accuracy:'86%', color:'#F59E0B', group:'Celestial Empire' },
  { id:8, rank:8, name:'Mariam Saleh', xp:2480, level:10, badge:'⭐', faculty:'Microbiology', wins:16, accuracy:'84%', color:'#EF4444', group:'Mystic Mermaid' },
  { id:9, rank:9, name:'Kareem Nasser', xp:2210, level:9, badge:'⭐', faculty:'Medical Lab', wins:14, accuracy:'82%', color:'#EC4899', group:'Phoenix Rising' },
  { id:10, rank:10, name:'Lina Al-Ahmad', xp:1980, level:8, badge:'⭐', faculty:'Urinalysis', wins:11, accuracy:'80%', color:'#00D4FF', group:'Shadow Wolves' },
];

export const LEADERBOARD = MOCK_LEADERBOARD.slice(0, 3);

export const MOCK_CHAT_MESSAGES = {
  g1: [
    { id:1, user:'Ahmed Al-Rashidi', text:'Just analyzed Fasciolopsis buski — got 97% confidence! The model is incredible 🦠', time:'10:24', avatar:'🧑‍🔬' },
    { id:2, user:'Sara Mohammed', text:'Amazing result! I detected Ascaris lumbricoides in my latest scan. 11 species detection is impressive 💪', time:'10:26', avatar:'👩‍🔬' },
    { id:3, user:'Omar Khalil', text:'What magnification works best for parasite eggs?', time:'10:28', avatar:'🧑‍💻' },
    { id:4, user:'Ahmed Al-Rashidi', text:'40x objective gives best clarity. Make sure the slide is well-stained with Giemsa or Lugol iodine 🔬', time:'10:30', avatar:'🧑‍🔬' },
    { id:5, user:'Fatima Al-Zahra', text:'The Gemini AI clinical report explains the pathophysiology so clearly! Game changer for studying 🔥', time:'10:35', avatar:'👩‍⚕️' },
    { id:6, user:'Ali Hassan', text:'Agreed! Treatment recommendations are spot on — Praziquantel dosing was exactly right', time:'10:38', avatar:'🧑‍⚕️' },
    { id:7, user:'Nour Ibrahim', text:'Dragon Syndicate is dominating the leaderboard this week! Keep it up team 🐉', time:'10:42', avatar:'👩‍🔬' },
  ],
  g2: [
    { id:1, user:'Youssef Ahmad', text:'Studying sickle cell detection pipeline — the async Celery processing is impressive! 🩸', time:'09:15', avatar:'🧑‍⚕️' },
    { id:2, user:'Mariam Saleh', text:'Current accuracy is 82% mAP — they are working on CNN v4 for improvement', time:'09:18', avatar:'👩‍🔬' },
    { id:3, user:'Youssef Ahmad', text:'The 9-stage pipeline is really thorough — quality gate, YOLO tiling, watershed declustering...', time:'09:22', avatar:'🧑‍⚕️' },
    { id:4, user:'Kareem Nasser', text:'RBC morphology overlay helps a lot with understanding cell shapes 🔴', time:'09:45', avatar:'🧑‍💻' },
    { id:5, user:'Lina Al-Ahmad', text:'Celestial Empire rising! 3 wins today in battle arena ⭐', time:'09:50', avatar:'👩‍💻' },
  ],
  g3: [
    { id:1, user:'Omar Khalil', text:'Gram stain today — G+ Coccus vs G- Bacillus classification is very accurate 🧫', time:'11:00', avatar:'🧑‍🔬' },
    { id:2, user:'Fatima Al-Zahra', text:'88.6% mAP for microbiology — really good for 4-class detection!', time:'11:05', avatar:'👩‍⚕️' },
    { id:3, user:'Ali Hassan', text:'Staphylococcus aureus detection was spot on in my sample', time:'11:10', avatar:'🧑‍⚕️' },
    { id:4, user:'Omar Khalil', text:'Mystic Mermaid stays in top 3! 🧜 Practice battle tonight?', time:'11:15', avatar:'🧑‍🔬' },
  ],
  g4: [
    { id:1, user:'Sara Mohammed', text:'Normal urine sediment reference: RBC 0-2/hpf, WBC 0-5/hpf, Ep cells 0-5/hpf 💧', time:'08:30', avatar:'👩‍🔬' },
    { id:2, user:'Ahmed Al-Rashidi', text:'What about cast reference ranges?', time:'08:32', avatar:'🧑‍🔬' },
    { id:3, user:'Sara Mohammed', text:'Hyaline casts 0-2/lpf is normal. Granular or RBC casts indicate serious pathology — always report!', time:'08:35', avatar:'👩‍🔬' },
    { id:4, user:'Nour Ibrahim', text:'Urinalysis model got 79.4% — pus cells detection could improve but overall solid', time:'08:40', avatar:'👩‍🔬' },
  ],
  g5: [
    { id:1, user:'Kareem Nasser', text:'Clinical report generation with Gemini AI is now active! 🤖 The pathophysiology section is excellent', time:'14:00', avatar:'🧑‍💻' },
    { id:2, user:'Lina Al-Ahmad', text:'Just got my first AI-enhanced report — Treatment recommendations are clinically accurate', time:'14:05', avatar:'👩‍💻' },
  ],
  g6: [
    { id:1, user:'Youssef Ahmad', text:'Training YOLOv8 on new parasite dataset — 1500+ images per class', time:'16:00', avatar:'🧑‍⚕️' },
    { id:2, user:'Mariam Saleh', text:'Data augmentation with rotation and HSV variation is key for robustness', time:'16:08', avatar:'👩‍🔬' },
  ],
  g7: [
    { id:1, user:'Ahmed Al-Rashidi', text:'مرحباً بالجميع في مجتمع طلاب الطب العراق! 🎓', time:'12:00', avatar:'🧑‍🔬' },
    { id:2, user:'Fatima Al-Zahra', text:'أهلاً! تطبيق LabMind AI يساعدنا كثيراً في دراسة علم الطفيليات', time:'12:05', avatar:'👩‍⚕️' },
    { id:3, user:'Omar Khalil', text:'نعم! خاصة ميزة التقرير السريري بالذكاء الاصطناعي رائعة جداً 🔬', time:'12:10', avatar:'🧑‍💻' },
  ],
  g8: [
    { id:1, user:'Ali Hassan', text:'Battle Arena tonight at 8PM! Hematology quiz — who is in? ⚔️', time:'17:00', avatar:'🧑‍⚕️' },
    { id:2, user:'Nour Ibrahim', text:'I am ready! Studied CBC analysis all day 🩸', time:'17:05', avatar:'👩‍🔬' },
    { id:3, user:'Lina Al-Ahmad', text:'Count me in! Shadow Wolves never back down 🐺', time:'17:08', avatar:'👩‍💻' },
  ],
};

/* ─── Utility: Faction color lookup ─── */
export const getGroupColor = (type) => {
    const name = (typeof type === 'string' ? type : (type?.iconName || type?.name || type?.icon || '')).toLowerCase();
    if (name.includes('dragon')) return '#ff3131';
    if (name.includes('crown') || name.includes('celestial')) return '#00ffff';
    if (name.includes('mermaid') || name.includes('mystic')) return '#ff00ff';
    if (name.includes('beast') || name.includes('monster') || name.includes('toxic')) return '#39ff14';
    if (name.includes('robot') || name.includes('cyber') || name.includes('mecha')) return '#0080ff';
    if (name.includes('unicorn') || name.includes('astral')) return '#a855f7';
    if (name.includes('alien') || name.includes('galactic') || name.includes('invader')) return '#10b981';
    if (name.includes('ghost') || name.includes('phantom') || name.includes('assassin')) return '#ffffff';
    return '#00ffff';
};

/* ─── Utility: hex to rgba ─── */
export const hex2rgba = (hex, alpha = 1) => {
    const [r, g, b] = hex.match(/\w\w/g).map(x => parseInt(x, 16));
    return `rgba(${r},${g},${b},${alpha})`;
};

/* ─── Utility: Icon theme mapping ─── */
export const ICON_THEMES = {
    dragon: { color: '#ef4444', path: "", image: '/icons/faction_dragon_1772453850935.png' },
    crown: { color: '#fbbf24', path: "", image: '/icons/faction_crown_1772453867665.png' },
    siren: { color: '#f472b6', path: "", image: '/icons/faction_mermaid_1772453891519.png' },
    wolf: { color: '#10b981', path: "", image: '/icons/faction_wolf_1772454883587.png' },
    raven: { color: '#f3f4f6', path: "", image: '/icons/faction_raven_1772454901330.png' },
    knight: { color: '#a855f7', path: "", image: '/icons/faction_knight_1772455092194.png' },
    mage: { color: '#4ade80', path: "", image: '/icons/faction_mage_1772455183138.png' },
    golem: { color: '#3b82f6', path: "", image: '/icons/faction_golem_1772455199984.png' },
    "epic neon fire dragon": { color: '#ef4444', path: "", image: '/icons/faction_dragon_1772453850935.png' },
    "giant glowing frost wolf": { color: '#3b82f6', path: "", image: '/icons/faction_wolf_1772454883587.png' },
    "dark shadow knight": { color: '#8b5cf6', path: "", image: '/icons/faction_knight_1772455092194.png' },
    "mythical deep sea siren": { color: '#d946ef', path: "", image: '/icons/faction_mermaid_1772453891519.png' },
    "celestial angelic valkyrie": { color: '#fbbf24', path: "", image: '/icons/faction_valkyrie_1772463041309.png' },
};

/* ─── Utility: resolve theme key from name ─── */
export const resolveThemeKey = (type) => {
    const name = (typeof type === 'string' ? type : (type?.iconName || type?.name || '')).toLowerCase();
    if (ICON_THEMES[name]) return name;
    if (name.includes('dragon')) return "dragon";
    if (name.includes('crown') || name.includes('celestial') || name.includes('empire')) return "crown";
    if (name.includes('mermaid') || name.includes('siren') || name.includes('water')) return "siren";
    if (name.includes('wolf') || name.includes('beast')) return "wolf";
    if (name.includes('golem') || name.includes('mecha') || name.includes('robot')) return "golem";
    if (name.includes('unicorn') || name.includes('knight') || name.includes('astral')) return "knight";
    if (name.includes('mage') || name.includes('alien') || name.includes('invader')) return "mage";
    if (name.includes('raven') || name.includes('shadow') || name.includes('assassin') || name.includes('phantom')) return "raven";
    return "dragon";
};

/* ─── Utility: get faction image path for card backgrounds ─── */
export const getGroupImage = (type) => {
    const name = (typeof type === 'string' ? type : (type?.iconName || type?.name || type?.icon || '')).toLowerCase();
    if (name.includes('crown') || name.includes('celestial') || name.includes('empire') || name.includes('valkyrie')) return '/icons/faction_valkyrie_1772463041309.png';
    if (name.includes('mermaid') || name.includes('siren') || name.includes('water')) return '/icons/faction_mermaid_1772453891519.png';
    if (name.includes('wolf') || name.includes('beast')) return '/icons/faction_wolf_1772454883587.png';
    if (name.includes('golem') || name.includes('mecha') || name.includes('robot')) return '/icons/faction_golem_1772455199984.png';
    if (name.includes('unicorn') || name.includes('knight') || name.includes('astral')) return '/icons/faction_knight_1772455092194.png';
    if (name.includes('alien') || name.includes('galactic') || name.includes('invader') || name.includes('mage')) return '/icons/faction_mage_1772455183138.png';
    if (name.includes('ghost') || name.includes('phantom') || name.includes('assassin') || name.includes('raven') || name.includes('shadow')) return '/icons/faction_raven_1772454901330.png';
    return '/icons/faction_dragon_1772453850935.png';
};
