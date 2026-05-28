/* ═══════════════════════════════════════════════════════════════
   VAULT DB — IndexedDB persistence layer for uploaded PDF files
   Stores file Blobs directly (no 5MB localStorage limit)
   ═══════════════════════════════════════════════════════════════ */

const DB_NAME = 'CurriculumVault';
const DB_VERSION = 1;
const STORE_NAME = 'documents';

function openDB() {
    return new Promise((resolve, reject) => {
        const request = indexedDB.open(DB_NAME, DB_VERSION);

        request.onupgradeneeded = (e) => {
            const db = e.target.result;
            if (!db.objectStoreNames.contains(STORE_NAME)) {
                const store = db.createObjectStore(STORE_NAME, { keyPath: 'id' });
                store.createIndex('stageId', 'stageId', { unique: false });
            }
        };

        request.onsuccess = () => resolve(request.result);
        request.onerror = () => reject(request.error);
    });
}

/**
 * Save a document record to IndexedDB.
 * Converts the File object to an ArrayBuffer for reliable storage.
 * @param {{ id: string, name: string, fileName: string, fileSize: string, stageId: number, timestamp: string, file: File }} doc
 */
export async function saveDocument(doc) {
    const db = await openDB();
    // Convert the File/Blob to an ArrayBuffer for safe IDB storage
    const arrayBuffer = await doc.file.arrayBuffer();

    const record = {
        id: doc.id,
        name: doc.name,
        fileName: doc.fileName,
        fileSize: doc.fileSize,
        stageId: doc.stageId,
        timestamp: doc.timestamp,
        fileData: arrayBuffer,       // raw binary
        fileType: doc.file.type || 'application/pdf',
        isPinned: doc.isPinned || false,
    };

    return new Promise((resolve, reject) => {
        const tx = db.transaction(STORE_NAME, 'readwrite');
        tx.objectStore(STORE_NAME).put(record);
        tx.oncomplete = () => resolve();
        tx.onerror = () => reject(tx.error);
    });
}

/**
 * Load ALL documents from IndexedDB.
 * Re-hydrates the ArrayBuffer back into a File object so the rest
 * of the app can use URL.createObjectURL(file) seamlessly.
 * @returns {Promise<Array>} Array of document objects with `file` as a File instance.
 */
export async function loadAllDocuments() {
    const db = await openDB();
    return new Promise((resolve, reject) => {
        const tx = db.transaction(STORE_NAME, 'readonly');
        const request = tx.objectStore(STORE_NAME).getAll();

        request.onsuccess = () => {
            const records = request.result.map(r => ({
                id: r.id,
                name: r.name,
                fileName: r.fileName,
                fileSize: r.fileSize,
                stage: r.stageId,
                timestamp: r.timestamp,
                isPinned: r.isPinned || false,
                // Reconstruct a File from the stored ArrayBuffer
                file: new File([r.fileData], r.fileName, { type: r.fileType }),
            }));
            resolve(records);
        };
        request.onerror = () => reject(request.error);
    });
}

/**
 * Delete a single document by ID.
 * @param {string} id
 */
export async function deleteDocument(id) {
    const db = await openDB();
    return new Promise((resolve, reject) => {
        const tx = db.transaction(STORE_NAME, 'readwrite');
        tx.objectStore(STORE_NAME).delete(id);
        tx.oncomplete = () => resolve();
        tx.onerror = () => reject(tx.error);
    });
}

/**
 * Toggle the pinned status of a document.
 * @param {string} id 
 * @param {boolean} isPinned 
 */
export async function togglePinStatus(id, isPinned) {
    const db = await openDB();
    return new Promise((resolve, reject) => {
        const tx = db.transaction(STORE_NAME, 'readwrite');
        const store = tx.objectStore(STORE_NAME);
        const getReq = store.get(id);

        getReq.onsuccess = () => {
            const record = getReq.result;
            if (record) {
                record.isPinned = isPinned;
                store.put(record);
                resolve();
            } else {
                reject(new Error("Document not found"));
            }
        };
        getReq.onerror = () => reject(getReq.error);
    });
}
