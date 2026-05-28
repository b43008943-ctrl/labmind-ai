import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import BookReader from '../components/library/BookReader';
import ImageReader from '../components/library/ImageReader';
import { useAuth } from '../context/AuthContext';

// Combined Library Catalog
const books = [
  // ── MEDICAL LAB — Year 1 ──
  {
    id: 1, category: 'Medical Lab', year_level: 'Year 1',
    title: 'Clinical Laboratory Science Review',
    author: 'Patsy Jarreau', year: '2004', pages: '400+', icon: '🔬',
    color: '#00D4FF',
    description: 'Comprehensive review for medical laboratory science students covering all major disciplines.',
    url: 'https://archive.org/details/clinicallaborato0000jarr',
    pdfUrl: 'https://archive.org/download/clinicallaborato0000jarr/clinicallaborato0000jarr.pdf',
    source: 'Archive.org', free: true, license: 'Public Domain',
    coverColor: '#1a2a3a', textColor: '#7ab8f5'
  },
  {
    id: 2, category: 'Medical Lab', year_level: 'Year 1',
    title: 'Basic Medical Microbiology',
    author: 'Baron S. — NIH', year: '2019', pages: '500+', icon: '🧫',
    color: '#00D4FF',
    description: 'Essential microbiology for first year students. Covers bacteria, viruses and fungi.',
    url: 'https://www.ncbi.nlm.nih.gov/books/NBK8099/',
    pdfUrl: '/books/microbiology-compressed.pdf',
    source: 'NIH/NCBI', free: true, isLocal: true,
    pageFolder: 'microbiology', totalPages: 1317,
    coverImage: '/book-covers/microbiology.svg'
  },
  {
    id: 3, category: 'Medical Lab', year_level: 'Year 1',
    title: 'Human Anatomy & Physiology — OpenStax',
    author: 'OpenStax College', year: '2022', pages: '1300+', icon: '🫀',
    color: '#00D4FF',
    description: 'Complete anatomy and physiology textbook. Essential foundation for all lab students.',
    url: 'https://openstax.org/details/books/anatomy-and-physiology-2e',
    pdfUrl: '/books/anatomy-compressed.pdf',
    source: 'OpenStax', free: true, isLocal: true,
    pageFolder: 'anatomy', totalPages: 1420,
    coverImage: '/book-covers/anatomy.svg'
  },
  {
    id: 4, category: 'Medical Lab', year_level: 'Year 1',
    title: 'Chemistry: Atoms First — OpenStax',
    author: 'OpenStax College', year: '2021', pages: '900+', icon: '⚗️',
    color: '#00D4FF',
    description: 'General chemistry for medical lab students covering atoms, molecules and reactions.',
    url: 'https://openstax.org/details/books/chemistry-atoms-first-2e',
    pdfUrl: '/books/chemistry-compressed.pdf',
    source: 'OpenStax', free: true, isLocal: true,
    pageFolder: 'chemistry', totalPages: 1331,
    coverImage: '/book-covers/chemistry.svg'
  },
  {
    id: 5, category: 'Medical Lab', year_level: 'Year 1',
    title: 'Biology — OpenStax',
    author: 'OpenStax College', year: '2022', pages: '1400+', icon: '🧬',
    color: '#00D4FF',
    description: 'Complete biology textbook covering cell biology, genetics, and physiology.',
    url: 'https://openstax.org/details/books/biology-2e',
    pdfUrl: '/books/biology-compressed.pdf',
    source: 'OpenStax', free: true, isLocal: true,
    pageFolder: 'biology', totalPages: 1578,
    coverImage: '/book-covers/biology.svg'
  },

  // ── MEDICAL LAB — Year 2 ──
  {
    id: 6, category: 'Medical Lab', year_level: 'Year 2',
    title: 'Hematology in Practice',
    author: 'Betty Ciesla', year: '2011', pages: '400+', icon: '🩸',
    color: '#EF4444',
    description: 'Practical guide to hematology — CBC interpretation and blood cell morphology.',
    url: 'https://archive.org/details/hematologyinprac00cies',
    pdfUrl: 'https://archive.org/download/hematologyinprac00cies/hematologyinprac00cies.pdf',
    source: 'Archive.org', free: true, license: 'Public Domain',
    coverColor: '#2a1a1a', textColor: '#e07070'
  },
  {
    id: 7, category: 'Medical Lab', year_level: 'Year 2',
    title: 'Medical Parasitology',
    author: 'Robert Beaver', year: '2003', pages: '400+', icon: '🦠',
    color: '#EF4444',
    description: 'Complete parasitology reference — identification, life cycles, and lab diagnosis.',
    url: 'https://archive.org/details/clinicalparasito0000bren',
    pdfUrl: 'https://archive.org/download/clinicalparasito0000bren/clinicalparasito0000bren.pdf',
    source: 'Archive.org', free: true, license: 'Public Domain',
    coverColor: '#2a1a2a', textColor: '#c870c8'
  },
  {
    id: 8, category: 'Medical Lab', year_level: 'Year 2',
    title: 'Urinalysis and Body Fluids',
    author: 'Susan King Strasinger', year: '2008', pages: '300+', icon: '🧪',
    color: '#EF4444',
    description: 'The definitive urinalysis textbook — physical, chemical, and microscopic examination.',
    url: 'https://archive.org/details/urinalysisbodyfl00stra',
    pdfUrl: 'https://archive.org/download/urinalysisbodyfl00stra/urinalysisbodyfl00stra.pdf',
    source: 'Archive.org', free: true, license: 'Public Domain',
    coverColor: '#1a2a1a', textColor: '#70c870'
  },
  {
    id: 9, category: 'Medical Lab', year_level: 'Year 2',
    title: 'Microbiology — OpenStax',
    author: 'OpenStax College', year: '2022', pages: '1000+', icon: '🦠',
    color: '#EF4444',
    description: 'Free OpenStax microbiology — bacteria, viruses, fungi, and lab techniques.',
    url: 'https://openstax.org/details/books/microbiology',
    pdfUrl: 'https://assets.openstax.org/oscms-prodcms/media/documents/Microbiology-WEB.pdf',
    source: 'OpenStax', free: true, license: 'CC BY 4.0',
    coverColor: '#122244', textColor: '#7ab8f5'
  },
  {
    id: 10, category: 'Medical Lab', year_level: 'Year 2',
    title: 'WHO Laboratory Manual',
    author: 'World Health Organization', year: '2009', pages: '400+', icon: '📋',
    color: '#EF4444',
    description: 'WHO lab manual — 5th edition. Basic techniques for health laboratories.',
    url: 'https://archive.org/details/who-laboratory-manual',
    pdfUrl: 'https://apps.who.int/iris/bitstream/handle/10665/44261/9789241547789_eng.pdf',
    source: 'WHO', free: true, license: 'WHO Open',
    coverColor: '#1a1a2a', textColor: '#9b72cf'
  },

  // ── MEDICAL LAB — Year 3 ──
  {
    id: 11, category: 'Medical Lab', year_level: 'Year 3',
    title: 'Clinical Chemistry',
    author: 'Michael L. Bishop', year: '2010', pages: '600+', icon: '⚗️',
    color: '#8B5CF6',
    description: 'Principles, procedures, and correlations — standard clinical chemistry reference.',
    url: 'https://archive.org/details/clinicalchemistr00bish',
    pdfUrl: 'https://archive.org/download/clinicalchemistr00bish/clinicalchemistr00bish.pdf',
    source: 'Archive.org', free: true, license: 'Public Domain',
    coverColor: '#2a2a1a', textColor: '#c8c870'
  },
  {
    id: 12, category: 'Medical Lab', year_level: 'Year 3',
    title: 'Blood Banking & Transfusion',
    author: 'John Harmening', year: '2012', pages: '500+', icon: '🩸',
    color: '#8B5CF6',
    description: 'Modern blood banking — ABO, compatibility testing, blood components.',
    url: 'https://archive.org/details/modernbloodbankintransfusion',
    pdfUrl: 'https://archive.org/download/modernbloodbankintransfusion/modernbloodbankintransfusion.pdf',
    source: 'Archive.org', free: true, license: 'Public Domain',
    coverColor: '#2a1a1a', textColor: '#e07070'
  },
  {
    id: 13, category: 'Medical Lab', year_level: 'Year 3',
    title: 'Immunology and Serology',
    author: 'Stevens & Miller', year: '2011', pages: '400+', icon: '🛡️',
    color: '#8B5CF6',
    description: 'Clinical immunology — antibody testing, autoimmune diseases, lab methods.',
    url: 'https://archive.org/details/clinicalimmunolo00stev',
    pdfUrl: 'https://archive.org/download/clinicalimmunolo00stev/clinicalimmunolo00stev.pdf',
    source: 'Archive.org', free: true, license: 'Public Domain',
    coverColor: '#1a1a2a', textColor: '#9b72cf'
  },
  {
    id: 14, category: 'Medical Lab', year_level: 'Year 3',
    title: 'Histology for Pathologists',
    author: 'Stephen Sternberg', year: '1997', pages: '500+', icon: '🔭',
    color: '#8B5CF6',
    description: 'Comprehensive histology — tissue preparation, staining, and interpretation.',
    url: 'https://archive.org/details/histologyforpath00ster',
    pdfUrl: 'https://archive.org/download/histologyforpath00ster/histologyforpath00ster.pdf',
    source: 'Archive.org', free: true, license: 'Public Domain',
    coverColor: '#1a2a2a', textColor: '#70c8c8'
  },
  {
    id: 15, category: 'Medical Lab', year_level: 'Year 3',
    title: 'Laboratory Management',
    author: 'Lynne Garcia', year: '2014', pages: '350+', icon: '📊',
    color: '#8B5CF6',
    description: 'Clinical laboratory management — quality systems, accreditation, operations.',
    url: 'https://archive.org/details/clinicallabmanagement',
    pdfUrl: 'https://archive.org/download/clinicallabmanagement/clinicallabmanagement.pdf',
    source: 'Archive.org', free: true, license: 'Public Domain',
    coverColor: '#2a2a2a', textColor: '#c8c8c8'
  },

  // ── MEDICAL LAB — Year 4 ──
  {
    id: 16, category: 'Medical Lab', year_level: 'Year 4',
    title: 'Quality Management in Labs',
    author: 'World Health Organization', year: '2011', pages: '300+', icon: '✅',
    color: '#F59E0B',
    description: 'WHO LQMS handbook — laboratory quality management system guidelines.',
    url: 'https://archive.org/details/who-lqms-handbook',
    pdfUrl: 'https://apps.who.int/iris/bitstream/handle/10665/44665/9789241548274_eng.pdf',
    source: 'WHO', free: true, license: 'WHO Open',
    coverColor: '#1a2a1a', textColor: '#70c870'
  },
  {
    id: 17, category: 'Medical Lab', year_level: 'Year 4',
    title: 'Molecular Diagnostics',
    author: 'Coleman & Tsongalis', year: '2006', pages: '400+', icon: '🧬',
    color: '#F59E0B',
    description: 'Fundamentals of molecular diagnostics — PCR, sequencing, clinical applications.',
    url: 'https://archive.org/details/moleculardiagnos00cole',
    pdfUrl: 'https://archive.org/download/moleculardiagnos00cole/moleculardiagnos00cole.pdf',
    source: 'Archive.org', free: true, license: 'Public Domain',
    coverColor: '#1a1a2a', textColor: '#7070e0'
  },
  {
    id: 18, category: 'Medical Lab', year_level: 'Year 4',
    title: 'Clinical Toxicology',
    author: 'Leikin & Paloucek', year: '2008', pages: '500+', icon: '☠️',
    color: '#F59E0B',
    description: 'Clinical toxicology — poison identification, lab testing, treatment protocols.',
    url: 'https://archive.org/details/clinicaltoxicolo00leik',
    pdfUrl: 'https://archive.org/download/clinicaltoxicolo00leik/clinicaltoxicolo00leik.pdf',
    source: 'Archive.org', free: true, license: 'Public Domain',
    coverColor: '#2a1a1a', textColor: '#e07070'
  },
  {
    id: 19, category: 'Medical Lab', year_level: 'Year 4',
    title: 'Point-of-Care Testing',
    author: 'Kost & Tran', year: '2010', pages: '200+', icon: '⚡',
    color: '#F59E0B',
    description: 'Principles of point-of-care testing — rapid diagnostics at patient bedside.',
    url: 'https://archive.org/details/principlesofpointofcare',
    pdfUrl: 'https://archive.org/download/principlesofpointofcare/principlesofpointofcare.pdf',
    source: 'Archive.org', free: true, license: 'Public Domain',
    coverColor: '#2a2a1a', textColor: '#c8c870'
  },
  {
    id: 20, category: 'Medical Lab', year_level: 'Year 4',
    title: 'Research Methods in Lab Science',
    author: 'Karen Munson', year: '2015', pages: '400+', icon: '📝',
    color: '#F59E0B',
    description: 'Research methodology for medical lab science — design, statistics, writing.',
    url: 'https://archive.org/details/researchmethodslab',
    pdfUrl: 'https://archive.org/download/researchmethodslab/researchmethodslab.pdf',
    source: 'Archive.org', free: true, license: 'Public Domain',
    coverColor: '#1a2a2a', textColor: '#70c8c8'
  },

  // ── SCIENTIFIC ──
  { id: 21, category: 'Scientific', title: 'Relativity', author: 'Albert Einstein', year: '1916', pages: '100+', source: 'Archive.org', free: true, coverImage: 'https://images.unsplash.com/photo-1462331940025-496dfbfc7564?auto=format&fit=crop&q=80&w=600', url: 'https://archive.org/details/relativityspecia00eins', description: 'Albert Einstein\'s original explanation of special and general relativity for lay readers.' },
  { id: 22, category: 'Scientific', title: 'Origin of Species', author: 'Charles Darwin', year: '1859', pages: '500+', source: 'Archive.org', free: true, coverImage: 'https://images.unsplash.com/photo-1532153975070-2e9ab71f1b14?auto=format&fit=crop&q=80&w=600', url: 'https://archive.org/details/originofspecies00darwuoft', description: 'Charles Darwin\'s foundation work of evolutionary biology, exploring natural selection.' },
  { id: 23, category: 'Scientific', title: 'Opticks', author: 'Isaac Newton', year: '1704', pages: '300+', source: 'Archive.org', free: true, coverImage: 'https://images.unsplash.com/photo-1507413245164-6160d8298b31?auto=format&fit=crop&q=80&w=600', url: 'https://archive.org/details/optickstreatise00newt', description: 'Isaac Newton\'s profound study on light, reflection, refraction, and color theory.' },
  { id: 24, category: 'Scientific', title: 'My Inventions', author: 'Nikola Tesla', year: '1919', pages: '100+', source: 'Archive.org', free: true, coverImage: 'https://images.unsplash.com/photo-1517420704952-d9f39e95b43e?auto=format&fit=crop&q=80&w=600', url: 'https://archive.org/details/myinventionsauto00tesl', description: 'Autobiographical reflections and revolutionary plans from Nikola Tesla.' },
  { id: 25, category: 'Scientific', title: 'Micrographia', author: 'Robert Hooke', year: '1665', pages: '200+', source: 'Archive.org', free: true, coverImage: 'https://images.unsplash.com/photo-1518152006812-edab29b069ac?auto=format&fit=crop&q=80&w=600', url: 'https://archive.org/details/micrographiaphy00hook', description: 'Robert Hooke\'s historic microscopic and telescopic observations containing beautiful drawings.' },
  { id: 26, category: 'Scientific', title: 'Astronomia Nova', author: 'Johannes Kepler', year: '1609', pages: '400+', source: 'Archive.org', free: true, coverImage: 'https://images.unsplash.com/photo-1419242902214-272b3f66ee7a?auto=format&fit=crop&q=80&w=600', url: 'https://archive.org/details/astronomianovaas00kepl', description: 'Johannes Kepler\'s presentation of his first two laws of planetary motion.' },
  { id: 27, category: 'Scientific', title: 'The Elements', author: 'Euclid', year: '300 BC', pages: '200+', source: 'Archive.org', free: true, coverImage: 'https://images.unsplash.com/photo-1509228468518-180dd4864904?auto=format&fit=crop&q=80&w=600', url: 'https://archive.org/details/euclidselements00eucl', description: 'The timeless mathematical textbook forming the baseline of geometry for 2,000 years.' },
  { id: 28, category: 'Scientific', title: 'De Humani Corporis', author: 'Andreas Vesalius', year: '1543', pages: '600+', source: 'Archive.org', free: true, coverImage: 'https://images.unsplash.com/photo-1582719471384-894fbb16e074?q=80&w=600', url: 'https://archive.org/details/dehumanicorporis00vesa', description: 'Andreas Vesalius\' monumental work on human anatomy, with detailed master engravings.' },

  // ── CULTURAL ──
  { id: 29, category: 'Cultural', title: 'Meditations', author: 'Marcus Aurelius', year: '180 AD', pages: '200+', source: 'Archive.org', free: true, coverImage: 'https://images.unsplash.com/photo-1600096194534-95cf5ece04cf?q=80&w=600', url: 'https://archive.org/details/meditations00auragoog', description: 'Stoic philosophy notes written by Roman Emperor Marcus Aurelius to himself.' },
  { id: 30, category: 'Cultural', title: 'The Art of War', author: 'Sun Tzu', year: '500 BC', pages: '100+', source: 'Archive.org', free: true, coverImage: 'https://images.unsplash.com/photo-1554147090-e124653d6a0c?q=80&w=600', url: 'https://archive.org/details/artofwar00sunt', description: 'The famous ancient Chinese military treatise attributed to Sun Tzu.' },
  { id: 31, category: 'Cultural', title: 'The Republic', author: 'Plato', year: '375 BC', pages: '300+', source: 'Archive.org', free: true, coverImage: 'https://images.unsplash.com/photo-1588534887556-324f2b1897c4?q=80&w=600', url: 'https://archive.org/details/republicofplato00platuoft', description: 'Socratic dialogue on justice, the order of the city-state, and the philosopher king.' },

  // ── SELF-DEVELOPMENT ──
  { id: 32, category: 'Self-Development', title: 'As a Man Thinketh', author: 'James Allen', year: '1903', pages: '50+', source: 'Archive.org', free: true, coverImage: 'https://images.unsplash.com/photo-1506126613408-eca07ce68773?q=80&w=600', url: 'https://archive.org/details/asmanthinketh00alle', description: 'James Allen\'s classic work on how thoughts dictate our reality and achievements.' },
  { id: 33, category: 'Self-Development', title: 'The Science of Getting Rich', author: 'Wallace D. Wattles', year: '1910', pages: '100+', source: 'Archive.org', free: true, coverImage: 'https://images.unsplash.com/photo-1611270418597-a6cbf50f686e?q=80&w=600', url: 'https://archive.org/details/scienceofgetting00watt', description: 'A practical, scientific approach to personal development and financial abundance.' },
  { id: 34, category: 'Self-Development', title: 'Art of Public Speaking', author: 'Dale Carnegie', year: '1915', pages: '400+', source: 'Archive.org', free: true, coverImage: 'https://images.unsplash.com/photo-1529333166437-7750a6dd5a70?q=80&w=600', url: 'https://archive.org/details/artofpublicspeak00carn', description: 'Dale Carnegie\'s essential textbook on persuasion, public speaking, and human connection.' },

  // ── MYTHOLOGY ──
  { id: 35, category: 'Mythology', title: 'The Iliad', author: 'Homer', year: '800 BC', pages: '400+', source: 'Archive.org', free: true, coverImage: 'https://images.unsplash.com/photo-1535905557558-afc4877a26fc?q=80&w=600', url: 'https://archive.org/details/iliadofhomer00home', description: 'Homer\'s epic poem recounting the final weeks of the Trojan War and the wrath of Achilles.' },
  { id: 36, category: 'Mythology', title: 'The Odyssey', author: 'Homer', year: '800 BC', pages: '300+', source: 'Archive.org', free: true, coverImage: 'https://images.unsplash.com/photo-1518364538175-115f013d2f93?q=80&w=600', url: 'https://archive.org/details/odysseyofhomer00home', description: 'Homer\'s epic journey of Odysseus as he struggles to return home to Ithaca.' },
  { id: 37, category: 'Mythology', title: 'Beowulf', author: 'Unknown', year: '1000 AD', pages: '200+', source: 'Archive.org', free: true, coverImage: 'https://images.unsplash.com/photo-1590792198083-d56d11f77d32?q=80&w=600', url: 'https://archive.org/details/beowulf00unknown', description: 'The heroic Old English epic poem detailing Beowulf\'s battle against the monster Grendel.' },

  // ── ROMANCE ──
  { id: 38, category: 'Romance', title: 'Pride and Prejudice', author: 'Jane Austen', year: '1813', pages: '350+', source: 'Archive.org', free: true, coverImage: 'https://images.unsplash.com/photo-1518621736915-f3b8c41bfd00?q=80&w=600', url: 'https://archive.org/details/prideprejudice00aust', description: 'Jane Austen\'s masterpiece tracking the turbulent relationship between Elizabeth Bennet and Mr. Darcy.' },
  { id: 39, category: 'Romance', title: 'Romeo and Juliet', author: 'William Shakespeare', year: '1597', pages: '150+', source: 'Archive.org', free: true, coverImage: 'https://images.unsplash.com/photo-1518895949257-7621bf27ecf6?q=80&w=600', url: 'https://archive.org/details/romeojuliet00shak', description: 'Shakespeare\'s tragedy of star-crossed young lovers in Verona.' },
  { id: 40, category: 'Romance', title: 'Wuthering Heights', author: 'Emily Brontë', year: '1847', pages: '300+', source: 'Archive.org', free: true, coverImage: 'https://images.unsplash.com/photo-1485600263604-a690ea50b691?q=80&w=600', url: 'https://archive.org/details/wutheringheights00bron', description: 'The passionate, gothic tale of Heathcliff and Catherine on the Yorkshire moors.' },

  // ── ISLAMIC ──
  { id: 41, category: 'Islamic', title: 'The Sealed Nectar', author: 'Safiur-Rahman Al-Mubarakpuri', description: 'Complete biography of Prophet Muhammad — award winning.', isLocal: false, pdfUrl: null, url: 'https://archive.org/details/the-sealed-nectar_202003', license: 'Public Domain', coverColor: '#0d2a1a', textColor: '#50c8a0', icon: '🌙', source: 'Archive.org', free: true },
  { id: 42, category: 'Islamic', title: 'Riyad as-Salihin', author: 'Imam Al-Nawawi', description: 'Gardens of the Righteous — classic hadith collection.', isLocal: false, pdfUrl: null, url: 'https://archive.org/details/RiyadhAsSaliheen', license: 'Public Domain', coverColor: '#1a2e0d', textColor: '#a0c850', icon: '📿', source: 'Archive.org', free: true },
  { id: 43, category: 'Islamic', title: "Don't Be Sad", author: 'Dr. Aid al-Qarni', description: 'Islamic guide to happiness and removing anxiety.', isLocal: false, pdfUrl: null, url: 'https://archive.org/details/DontBeSad_201608', license: 'Public Domain', coverColor: '#2a1a0d', textColor: '#c8a050', icon: '☀️', source: 'Archive.org', free: true },
  { id: 44, category: 'Islamic', title: 'The Beginning and the End', author: 'Ibn Kathir', description: 'History of the world from an Islamic perspective.', isLocal: false, pdfUrl: null, url: 'https://archive.org/details/TheBeginingAndTheEnd', license: 'Public Domain', coverColor: '#1a0d2e', textColor: '#9b72cf', icon: '📖', source: 'Archive.org', free: true },
  { id: 45, category: 'Islamic', title: 'Fortress of the Muslim', author: "Sa'id Al-Qahtani", description: 'Daily supplications and Dhikr from Quran and Sunnah.', isLocal: false, pdfUrl: null, url: 'https://archive.org/details/FortressOfTheMuslim', license: 'Public Domain', coverColor: '#0d1f2e', textColor: '#5ab4d4', icon: '🤲', source: 'Archive.org', free: true }
];

const initialBooks = books.map(book => {
  let cc = book.coverColor;
  let tc = book.textColor;
  if (!cc) {
    if (book.color) {
      if (book.color === '#00D4FF') {
        cc = '#0e2f3d';
        tc = '#00D4FF';
      } else if (book.color === '#EF4444') {
        cc = '#4a1515';
        tc = '#ff6b6b';
      } else if (book.color === '#8B5CF6') {
        cc = '#2a1a4a';
        tc = '#b89cff';
      } else if (book.color === '#F59E0B') {
        cc = '#4a320c';
        tc = '#ffcc66';
      } else {
        cc = '#1a1a2e';
        tc = '#e2e8f0';
      }
    } else {
      if (book.category === 'Scientific') {
        cc = '#132237';
        tc = '#60a5fa';
      } else if (book.category === 'Cultural' || book.category === 'Mythology') {
        cc = '#2d1b08';
        tc = '#fca5a5';
      } else if (book.category === 'Romance') {
        cc = '#3b0b13';
        tc = '#fda4af';
      } else if (book.category === 'Self-Development') {
        cc = '#062c16';
        tc = '#86efac';
      } else {
        cc = '#1e1e2f';
        tc = '#f8fafc';
      }
    }
  }

  // Determine default rating
  let defaultRating = 4.0;
  if (book.id === 2) defaultRating = 4.2;
  else if (book.id === 3) defaultRating = 4.6;
  else if (book.id === 4) defaultRating = 4.0;
  else if (book.id === 5) defaultRating = 4.4;
  else {
    // Generate a consistent pseudo-random rating between 3.8 and 4.7 based on book ID
    const pseudoRand = ((book.id * 9301 + 49297) % 233280) / 233280;
    defaultRating = Math.round((3.8 + pseudoRand * 0.9) * 10) / 10;
  }

  // Load user rating if exists in localStorage
  const userRating = localStorage.getItem(`labmind_book_${book.id}_userrating`);
  const finalRating = userRating ? parseFloat(userRating) : defaultRating;

  return {
    ...book,
    coverColor: cc,
    textColor: tc,
    progress: 0,
    rating: finalRating
  };
});

function darken(hex) {
  // simple darken — reduce each RGB channel
  const c = hex.replace('#','');
  const r = Math.max(0, parseInt(c.substr(0,2),16) - 40);
  const g = Math.max(0, parseInt(c.substr(2,2),16) - 40);
  const b = Math.max(0, parseInt(c.substr(4,2),16) - 40);
  return `rgb(${r},${g},${b})`;
}

function StarRating({ rating, bookId, editable, onRate, size }) {
  const [hover, setHover] = useState(0)
  const starSize = size || 16
  const display = hover || rating

  return (
    <div style={{ 
      display: 'flex', 
      gap: 3, 
      alignItems: 'center'
    }}>
      {[1,2,3,4,5].map(i => (
        <span
          key={i}
          onClick={editable ? () => onRate(i) : undefined}
          onMouseEnter={editable ? () => setHover(i) : undefined}
          onMouseLeave={editable ? () => setHover(0) : undefined}
          style={{
            fontSize: starSize,
            lineHeight: 1,
            color: i <= Math.round(display) ? '#f0b429' : '#3a3631',
            cursor: editable ? 'pointer' : 'default',
            transition: 'color 0.15s, transform 0.15s',
            transform: (editable && hover === i) ? 'scale(1.2)' : 'scale(1)',
            userSelect: 'none'
          }}
        >★</span>
      ))}
      {!editable && (
        <span style={{ 
          fontSize: starSize * 0.7, 
          color: '#888', 
          marginRight: 5,
          fontWeight: 600
        }}>
          {rating.toFixed(1)}
        </span>
      )}
    </div>
  )
}

/* ════════════════════════════════════════
   MAIN LIBRARY COMPONENT
   ════════════════════════════════════════ */
export default function DigitalLibrary({ onReadingContextChange, onNavigate }) {
  const [activeCategory, setActiveCategory] = useState('الكل');
  const [activeYear, setActiveYear] = useState('الكل');
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedBook, setSelectedBook] = useState(null);
  const [showReader, setShowReader] = useState(false);
  const [readerVisible, setReaderVisible] = useState(false);
  const [booksState, setBooksState] = useState(initialBooks);
  const { currentUser } = useAuth();

  // Load progress and ratings from localStorage on mount
  useEffect(() => {
    const updatedBooks = initialBooks.map(book => {
      const savedProgress = localStorage.getItem(`labmind_book_${book.id}_progress`);
      const savedRating = localStorage.getItem(`labmind_book_${book.id}_userrating`);
      return {
        ...book,
        progress: savedProgress ? parseInt(savedProgress) : book.progress,
        rating: savedRating ? parseFloat(savedRating) : book.rating
      };
    });
    setBooksState(updatedBooks);
  }, []);

  const categories = [
    { name: 'الكل', icon: '📚' },
    { name: '🔬 مختبر', icon: '🔬' },
    { name: '⚗️ علوم', icon: '⚗️' },
    { name: '🌙 إسلامي', icon: '🌙' },
    { name: '📖 روايات', icon: '📖' },
    { name: '🏛️ فلسفة', icon: '🏛️' },
    { name: '🌱 تطوير', icon: '🌱' }
  ];

  const yearLevels = ['الكل', 'السنة ١', 'السنة ٢', 'السنة ٣', 'السنة ٤'];

  // Map Arabic years to the book database format
  const yearMapping = {
    'الكل': 'All Years',
    'السنة ١': 'Year 1',
    'السنة ٢': 'Year 2',
    'السنة ٣': 'Year 3',
    'السنة ٤': 'Year 4'
  };

  const filteredBooks = booksState.filter(book => {
    // Category filter mapping
    let catMatch = activeCategory === 'الكل';
    if (activeCategory === '🔬 مختبر') catMatch = book.category === 'Medical Lab';
    if (activeCategory === '⚗️ علوم') catMatch = book.category === 'Scientific';
    if (activeCategory === '🌙 إسلامي') catMatch = book.category === 'Islamic';
    if (activeCategory === '📖 روايات') catMatch = book.category === 'Romance';
    if (activeCategory === '🏛️ فلسفة') catMatch = book.category === 'Mythology' || book.category === 'Cultural';
    if (activeCategory === '🌱 تطوير') catMatch = book.category === 'Self-Development';

    // Year filter (applies only for Medical Lab category)
    const englishYear = yearMapping[activeYear];
    const yearMatch = activeCategory !== '🔬 مختبر' || activeYear === 'الكل' || book.year_level === englishYear;

    // Search query filter
    const searchMatch = !searchQuery ||
      book.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      book.author.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (book.description && book.description.toLowerCase().includes(searchQuery.toLowerCase()));

    return catMatch && yearMatch && searchMatch;
  });

  const continueReadingBooks = booksState.filter(b => b.progress > 0);

  const totalBooks = booksState.length;
  const localBooks = booksState.filter(b => b.isLocal).length;
  const onlineBooks = totalBooks - localBooks;
  const totalCategories = 6;

  // Resolve user avatar
  const userChar = (currentUser?.full_name || currentUser?.userName || currentUser?.email || 'ط').charAt(0).toUpperCase();

  const handleBookClick = (book) => {
    setSelectedBook(book);
    setShowReader(true);
    setTimeout(() => setReaderVisible(true), 10);
  };

  const handleCloseReader = () => {
    setReaderVisible(false);
    setTimeout(() => {
      setShowReader(false);
      setSelectedBook(null);
    }, 300);
  };

  const rateBook = (bookId, stars) => {
    localStorage.setItem(`labmind_book_${bookId}_userrating`, stars);
    setBooksState(prev => prev.map(book =>
      book.id === bookId ? { ...book, rating: stars } : book
    ));
  };

  // Sections definitions for sectioned layout
  const otherCategories = [
    {
      label: 'العلوم والطبيعة',
      icon: '⚗️',
      books: filteredBooks.filter(b => b.category === 'Scientific')
    },
    {
      label: 'الكتب الإسلامية',
      icon: '🌙',
      books: filteredBooks.filter(b => b.category === 'Islamic')
    },
    {
      label: 'الفلسفة والأساطير',
      icon: '🏛️',
      books: filteredBooks.filter(b => b.category === 'Mythology' || b.category === 'Cultural')
    },
    {
      label: 'الروايات والدراما',
      icon: '📖',
      books: filteredBooks.filter(b => b.category === 'Romance')
    },
    {
      label: 'التطوير الذاتي',
      icon: '🌱',
      books: filteredBooks.filter(b => b.category === 'Self-Development')
    }
  ];

  return (
    <div style={{
      minHeight: '100vh',
      background: '#080808',
      color: '#ffffff',
      fontFamily: '-apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif',
      paddingBottom: '120px',
      direction: 'rtl'
    }}>
      <style>{`
        .no-scrollbar::-webkit-scrollbar {
          display: none;
        }
        .no-scrollbar {
          -ms-overflow-style: none;
          scrollbar-width: none;
        }
        .featured-card:hover img {
          transform: scale(1.04);
        }
      `}</style>

      {/* ════════════════════════════════════════
         SECTION 1: HEADER
         ════════════════════════════════════════ */}
      <div style={{ padding: '20px 18px 0', width: '100%' }}>
        {/* Row 1 — Greetings & Avatar */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
          <div>
            <div style={{ fontSize: '11px', color: '#555555', fontWeight: 600, letterSpacing: '0.5px' }}>
              مرحباً، الطالبة 👋
            </div>
            <div style={{ fontSize: '24px', fontWeight: 800, color: '#ffffff', letterSpacing: '-0.5px', marginTop: '2px' }}>
              المكتبة
            </div>
          </div>

          <div style={{ display: 'flex', gap: '8px', alignItems: 'center' }}>
            {/* Back Button */}
            <button
              onClick={() => onNavigate && onNavigate('academic-hub')}
              style={{
                background: '#141414',
                border: 'none',
                borderRadius: '8px',
                color: '#aaaaaa',
                padding: '6px 12px',
                fontSize: '11px',
                fontWeight: 700,
                cursor: 'pointer',
                marginLeft: '8px'
              }}
            >
              الرئيسية
            </button>
            {/* User Avatar */}
            <div style={{
              width: '36px',
              height: '36px',
              borderRadius: '50%',
              background: 'linear-gradient(135deg, #c8860a, #e8a020)',
              color: '#000000',
              fontWeight: 800,
              fontSize: '15px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}>
              {userChar}
            </div>
          </div>
        </div>

        {/* Row 2 — Search input */}
        <div style={{ position: 'relative', marginBottom: '16px' }}>
          <input
            type="text"
            placeholder="ابحث عن كتاب أو مؤلف..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            style={{
              width: '100%',
              background: '#141414',
              border: 'none',
              borderRadius: '12px',
              padding: '12px 16px 12px 40px',
              color: '#ffffff',
              fontSize: '14px',
              outline: 'none',
              textAlign: 'right'
            }}
          />
          <span style={{
            position: 'absolute',
            left: '14px',
            top: '50%',
            transform: 'translateY(-50%)',
            color: '#444444',
            fontSize: '16px',
            pointerEvents: 'none'
          }}>🔍</span>
        </div>

        {/* Row 3 — Category pills */}
        <div className="no-scrollbar" style={{
          display: 'flex',
          gap: '8px',
          overflowX: 'auto',
          paddingBottom: '16px',
          width: '100%',
          scrollBehavior: 'smooth'
        }}>
          {categories.map(cat => {
            const isActive = activeCategory === cat.name;
            return (
              <button
                key={cat.name}
                onClick={() => {
                  setActiveCategory(cat.name);
                  setActiveYear('الكل'); // Reset sub-filter
                }}
                style={isActive ? {
                  background: '#c8860a',
                  color: '#000000',
                  padding: '7px 16px',
                  borderRadius: '20px',
                  fontSize: '12px',
                  fontWeight: 700,
                  border: 'none',
                  cursor: 'pointer',
                  whiteSpace: 'nowrap'
                } : {
                  background: '#141414',
                  color: '#888888',
                  padding: '7px 16px',
                  borderRadius: '20px',
                  fontSize: '12px',
                  fontWeight: 500,
                  border: 'none',
                  cursor: 'pointer',
                  whiteSpace: 'nowrap'
                }}
              >
                {cat.name}
              </button>
            );
          })}
        </div>
      </div>

      {/* ════════════════════════════════════════
         SECTION 2: CONTINUE READING (متابعة القراءة)
         ════════════════════════════════════════ */}
      {!searchQuery && continueReadingBooks.length > 0 && (
        <div style={{ marginTop: '16px', marginBottom: '24px' }}>
          <h2 style={{
            fontSize: '18px',
            fontWeight: 800,
            color: '#ffffff',
            letterSpacing: '-0.3px',
            padding: '0 18px',
            marginBottom: '12px',
            textAlign: 'right'
          }}>
            متابعة القراءة
          </h2>

          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fill, minmax(160px, 1fr))',
            gap: '10px',
            padding: '0 18px'
          }}>
            {continueReadingBooks.map(book => (
              <div
                key={book.id}
                onClick={() => handleBookClick(book)}
                style={{
                  background: '#111111',
                  borderRadius: '12px',
                  display: 'flex',
                  alignItems: 'center',
                  overflow: 'hidden',
                  cursor: 'pointer',
                  padding: '6px'
                }}
              >
                {/* Left Icon Square */}
                <div style={{
                  width: '52px',
                  height: '52px',
                  borderRadius: '8px',
                  background: book.coverColor || '#1a1a2e',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: '22px',
                  flexShrink: 0
                }}>
                  {book.icon || '📚'}
                </div>

                {/* Right Info */}
                <div style={{
                  flex: 1,
                  padding: '0 10px',
                  minWidth: 0,
                  textAlign: 'right'
                }}>
                  <div style={{
                    fontSize: '11px',
                    fontWeight: 700,
                    color: '#ffffff',
                    whiteSpace: 'nowrap',
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    marginBottom: '4px'
                  }}>
                    {book.title}
                  </div>
                  {/* Progress Bar */}
                  <div style={{
                    height: '2px',
                    background: '#1e1e1e',
                    borderRadius: '1px',
                    overflow: 'hidden',
                    width: '100%'
                  }}>
                    <div style={{
                      height: '100%',
                      background: '#c8860a',
                      width: `${book.progress}%`
                    }} />
                  </div>
                  <div style={{ fontSize: '10px', color: '#555555', marginTop: '3px', fontWeight: 600 }}>
                    {book.progress}%
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ════════════════════════════════════════
         SECTION 3: MEDICAL LAB FEATURED ROW
         ════════════════════════════════════════ */}
      {!searchQuery && (activeCategory === 'الكل' || activeCategory === '🔬 مختبر') && (
        <div style={{ marginBottom: '28px' }}>
          {/* Header Row */}
          <div style={{
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            padding: '0 18px',
            marginBottom: '12px'
          }}>
            <h2 style={{ fontSize: '18px', fontWeight: 800, color: '#ffffff' }}>🔬 المختبر الطبي</h2>
            <span style={{ fontSize: '12px', color: '#c8860a', cursor: 'pointer', fontWeight: 600 }}>عرض الكل</span>
          </div>

          {/* Year Filter Tabs */}
          <div style={{
            display: 'flex',
            gap: '6px',
            padding: '0 18px',
            marginBottom: '14px',
            overflowX: 'auto'
          }} className="no-scrollbar">
            {yearLevels.map(year => {
              const isActive = activeYear === year;
              return (
                <button
                  key={year}
                  onClick={() => setActiveYear(year)}
                  style={isActive ? {
                    background: '#1a1a1a',
                    color: '#c8860a',
                    border: '1px solid rgba(200,134,10,0.15)',
                    padding: '5px 12px',
                    borderRadius: '8px',
                    fontSize: '11px',
                    fontWeight: 700,
                    cursor: 'pointer',
                    whiteSpace: 'nowrap'
                  } : {
                    background: '#111111',
                    color: '#555555',
                    border: 'none',
                    padding: '5px 12px',
                    borderRadius: '8px',
                    fontSize: '11px',
                    fontWeight: 700,
                    cursor: 'pointer',
                    whiteSpace: 'nowrap'
                  }}
                >
                  {year}
                </button>
              );
            })}
          </div>

          {/* Horizontal Scroll Row */}
          <div className="no-scrollbar" style={{
            display: 'flex',
            gap: '12px',
            overflowX: 'auto',
            padding: '0 18px',
            width: '100%'
          }}>
            {filteredBooks.filter(b => b.category === 'Medical Lab').map(book => (
              <div
                key={book.id}
                onClick={() => handleBookClick(book)}
                className="featured-card"
                style={{ width: '130px', cursor: 'pointer', flexShrink: 0, marginBottom: '16px' }}
              >
                {/* 3D cover container */}
                {book.coverImage ? (
                  <div style={{ perspective: '700px', width: 130, height: 188, marginBottom: '12px' }}>
                    <div style={{
                      width: 130, height: 188,
                      position: 'relative',
                      transformStyle: 'preserve-3d',
                      transform: 'rotateY(-15deg)',
                      transition: 'transform 0.45s'
                    }}
                    onMouseEnter={e => e.currentTarget.style.transform='rotateY(-22deg) translateY(-6px)'}
                    onMouseLeave={e => e.currentTarget.style.transform='rotateY(-15deg)'}
                    >
                      <img
                        src={book.coverImage}
                        alt={book.title}
                        style={{
                          width: '100%', height: '100%',
                          borderRadius: '3px 8px 8px 3px',
                          boxShadow: '0 14px 32px rgba(0,0,0,0.75)',
                          display: 'block'
                        }}
                      />
                    </div>
                  </div>
                ) : (
                  <div style={{ perspective: '600px', width: 130, height: 175, marginBottom: '12px' }}>
                    <div style={{
                      width: 130, height: 175,
                      position: 'relative',
                      transformStyle: 'preserve-3d',
                      transform: 'rotateY(-16deg)',
                      transition: 'transform 0.4s'
                    }}
                    onMouseEnter={e => e.currentTarget.style.transform='rotateY(-22deg) translateY(-6px)'}
                    onMouseLeave={e => e.currentTarget.style.transform='rotateY(-16deg)'}
                    >
                      {/* book front */}
                      <div style={{
                        position: 'absolute', width: '100%', height: '100%',
                        background: `linear-gradient(140deg, ${book.coverColor}, ${darken(book.coverColor)})`,
                        borderRadius: '3px 8px 8px 3px',
                        padding: '14px 12px',
                        display: 'flex', flexDirection: 'column',
                        justifyContent: 'space-between',
                        boxShadow: '0 12px 30px rgba(0,0,0,0.7)',
                        overflow: 'hidden'
                      }}>
                        {/* spine shadow (left edge) */}
                        <div style={{
                          position: 'absolute', left: 0, top: 0, bottom: 0,
                          width: 8,
                          background: 'linear-gradient(90deg, rgba(0,0,0,0.5), rgba(0,0,0,0.1))',
                          borderRadius: '3px 0 0 3px'
                        }} />
                        {/* light sheen (right edge) */}
                        <div style={{
                          position: 'absolute', right: 0, top: 0, bottom: 0,
                          width: 28,
                          background: 'linear-gradient(90deg, transparent, rgba(255,255,255,0.08))'
                        }} />
                        
                        {/* Top: Icon & Badge */}
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', width: '100%', zIndex: 1 }}>
                          <span style={{ fontSize: '28px' }}>{book.icon || '🔬'}</span>
                          <span style={book.isLocal ? {
                            background: '#c8860a',
                            color: '#000000',
                            padding: '2px 5px',
                            borderRadius: '4px',
                            fontSize: '7px',
                            fontWeight: 800
                          } : {
                            background: 'rgba(10,191,191,0.15)',
                            color: '#0abfbf',
                            padding: '2px 5px',
                            borderRadius: '4px',
                            fontSize: '7px',
                            fontWeight: 800
                          }}>
                            {book.isLocal ? 'PDF' : 'مجاني'}
                          </span>
                        </div>
                        
                        {/* Bottom Details (title + author) */}
                        <div style={{ zIndex: 1 }}>
                          <div style={{
                            fontSize: 10, fontWeight: 800,
                            color: book.textColor, lineHeight: 1.3,
                            overflow: 'hidden', textOverflow: 'ellipsis', display: '-webkit-box', WebkitLineClamp: 2, WebkitBoxOrient: 'vertical'
                          }}>{book.title}</div>
                          <div style={{
                            fontSize: 8, opacity: 0.6, marginTop: 3, color: '#fff',
                            whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis'
                          }}>{book.author}</div>
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                {/* Below Cover Metadata */}
                <div style={{ textAlign: 'right' }}>
                  <div style={{
                    fontSize: '12px',
                    fontWeight: 700,
                    color: '#ffffff',
                    whiteSpace: 'nowrap',
                    overflow: 'hidden',
                    textOverflow: 'ellipsis'
                  }}>
                    {book.title}
                  </div>
                  <div style={{ fontSize: '10px', color: '#555555', marginTop: '2px' }}>
                    {book.author} • {book.pages || 'N/A'}ص
                  </div>
                  <div style={{ marginTop: 6 }}>
                    <StarRating rating={book.rating} editable={false} size={13} />
                  </div>

                  {/* Progress Bar (if any progress) */}
                  {book.progress > 0 && (
                    <div style={{
                      height: '2px',
                      background: '#1e1e1e',
                      borderRadius: '1px',
                      overflow: 'hidden',
                      marginTop: '6px',
                      width: '100%'
                    }}>
                      <div style={{
                        height: '100%',
                        background: '#c8860a',
                        width: `${book.progress}%`
                      }} />
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ════════════════════════════════════════
         SECTION 4: OTHER CATEGORIES AS LISTS
         ════════════════════════════════════════ */}
      {!searchQuery && otherCategories.map(sec => {
        const isSectionActive = activeCategory === 'الكل' ||
          (activeCategory === '⚗️ علوم' && sec.label === 'العلوم والطبيعة') ||
          (activeCategory === '🌙 إسلامي' && sec.label === 'الكتب الإسلامية') ||
          (activeCategory === '🏛️ فلسفة' && sec.label === 'الفلسفة والأساطير') ||
          (activeCategory === '📖 روايات' && sec.label === 'الروايات والدراما') ||
          (activeCategory === '🌱 تطوير' && sec.label === 'التطوير الذاتي');

        if (!isSectionActive || sec.books.length === 0) return null;

        return (
          <div key={sec.label} style={{ marginBottom: '28px' }}>
            {/* Header Row */}
            <div style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              padding: '0 18px',
              marginBottom: '10px'
            }}>
              <h2 style={{ fontSize: '18px', fontWeight: 800, color: '#ffffff' }}>
                {sec.icon} {sec.label}
              </h2>
              <span style={{ fontSize: '12px', color: '#c8860a', cursor: 'pointer', fontWeight: 600 }}>عرض الكل</span>
            </div>

            {/* List items */}
            <div style={{ display: 'flex', flexDirection: 'column' }}>
              {sec.books.map((book, idx) => (
                <div key={book.id}>
                  <div
                    onClick={() => handleBookClick(book)}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '12px',
                      padding: '10px 18px',
                      cursor: 'pointer',
                      transition: 'background 0.2s',
                      justifyContent: 'space-between'
                    }}
                    onMouseEnter={(e) => { e.currentTarget.style.background = '#0f0f0f'; }}
                    onMouseLeave={(e) => { e.currentTarget.style.background = 'transparent'; }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flex: 1, minWidth: 0 }}>
                      {/* Number */}
                      <div style={{
                        fontSize: '13px',
                        color: '#333333',
                        width: '20px',
                        textAlign: 'center',
                        fontWeight: 600
                      }}>
                        {idx + 1}
                      </div>

                      {/* Icon Square */}
                      {book.coverImage ? (
                        <div style={{
                          width: '40px',
                          height: '58px',
                          borderRadius: '4px',
                          overflow: 'hidden',
                          flexShrink: 0,
                          boxShadow: '0 4px 10px rgba(0,0,0,0.5)'
                        }}>
                          <img
                            src={book.coverImage}
                            alt={book.title}
                            style={{ width: '100%', height: '100%', display: 'block' }}
                          />
                        </div>
                      ) : (
                        <div style={{
                          width: '46px',
                          height: '46px',
                          borderRadius: '8px',
                          background: book.coverColor || '#1e1e2f',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          fontSize: '20px',
                          flexShrink: 0
                        }}>
                          {book.icon || '📖'}
                        </div>
                      )}

                      {/* Info block */}
                      <div style={{ flex: 1, minWidth: 0, textAlign: 'right' }}>
                        <div style={{
                          fontSize: '13px',
                          fontWeight: 700,
                          color: '#ffffff',
                          whiteSpace: 'nowrap',
                          overflow: 'hidden',
                          textOverflow: 'ellipsis'
                        }}>
                          {book.title}
                        </div>
                        <div style={{ fontSize: '11px', color: '#555555', marginTop: '2px' }}>
                          {book.author} · {book.license || 'Public Domain'}
                        </div>
                        <div style={{ marginTop: 4 }}>
                          <StarRating rating={book.rating} editable={false} size={12} />
                        </div>
                      </div>
                    </div>

                    {/* Right Badge */}
                    <span style={book.isLocal ? {
                      background: 'rgba(200,134,10,0.15)',
                      color: '#c8860a',
                      padding: '3px 8px',
                      borderRadius: '6px',
                      fontSize: '9px',
                      fontWeight: 800
                    } : {
                      background: 'rgba(10,191,191,0.15)',
                      color: '#0abfbf',
                      padding: '3px 8px',
                      borderRadius: '6px',
                      fontSize: '9px',
                      fontWeight: 800
                    }}>
                      {book.isLocal ? 'محلي' : 'مجاني'}
                    </span>
                  </div>

                  {/* Divider */}
                  {idx < sec.books.length - 1 && (
                    <div style={{ height: '1px', background: '#111111', margin: '0 18px' }} />
                  )}
                </div>
              ))}
            </div>
          </div>
        );
      })}

      {/* ════════════════════════════════════════
         SECTION 6: SEARCH FLAT LIST (Active query)
         ════════════════════════════════════════ */}
      {searchQuery && (
        <div style={{ padding: '0 18px', marginTop: '16px' }}>
          <h2 style={{ fontSize: '16px', fontWeight: '800', color: '#ffffff', marginBottom: '16px', textAlign: 'right' }}>
            نتائج البحث ({filteredBooks.length})
          </h2>

          {filteredBooks.length === 0 ? (
            <div style={{ textAlign: 'center', padding: '40px 0', color: '#555555' }}>
              <span style={{ fontSize: '40px', display: 'block', marginBottom: '10px' }}>🪶</span>
              لا توجد نتائج تطابق بحثك.
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column' }}>
              {filteredBooks.map((book, idx) => (
                <div key={book.id}>
                  <div
                    onClick={() => handleBookClick(book)}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      gap: '12px',
                      padding: '10px 0',
                      cursor: 'pointer',
                      justifyContent: 'space-between'
                    }}
                  >
                    <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flex: 1, minWidth: 0 }}>
                      <div style={{
                        fontSize: '13px',
                        color: '#333333',
                        width: '20px',
                        textAlign: 'center',
                        fontWeight: 600
                      }}>
                        {idx + 1}
                      </div>

                      {/* Icon Square */}
                      {book.coverImage ? (
                        <div style={{
                          width: '40px',
                          height: '58px',
                          borderRadius: '4px',
                          overflow: 'hidden',
                          flexShrink: 0,
                          boxShadow: '0 4px 10px rgba(0,0,0,0.5)'
                        }}>
                          <img
                            src={book.coverImage}
                            alt={book.title}
                            style={{ width: '100%', height: '100%', display: 'block' }}
                          />
                        </div>
                      ) : (
                        <div style={{
                          width: '46px',
                          height: '46px',
                          borderRadius: '8px',
                          background: book.coverColor || '#1e1e2f',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          fontSize: '20px',
                          flexShrink: 0
                        }}>
                          {book.icon || '📖'}
                        </div>
                      )}

                      {/* Info block */}
                      <div style={{ flex: 1, minWidth: 0, textAlign: 'right' }}>
                        <div style={{
                          fontSize: '13px',
                          fontWeight: 700,
                          color: '#ffffff',
                          whiteSpace: 'nowrap',
                          overflow: 'hidden',
                          textOverflow: 'ellipsis'
                        }}>
                          {book.title}
                        </div>
                        <div style={{ fontSize: '11px', color: '#555555', marginTop: '2px' }}>
                          {book.author} · {book.category}
                        </div>
                        <div style={{ marginTop: 4 }}>
                          <StarRating rating={book.rating} editable={false} size={12} />
                        </div>
                      </div>
                    </div>

                    <span style={book.isLocal ? {
                      background: 'rgba(200,134,10,0.15)',
                      color: '#c8860a',
                      padding: '3px 8px',
                      borderRadius: '6px',
                      fontSize: '9px',
                      fontWeight: 800
                    } : {
                      background: 'rgba(10,191,191,0.15)',
                      color: '#0abfbf',
                      padding: '3px 8px',
                      borderRadius: '6px',
                      fontSize: '9px',
                      fontWeight: 800
                    }}>
                      {book.isLocal ? 'محلي' : 'مجاني'}
                    </span>
                  </div>

                  {idx < filteredBooks.length - 1 && (
                    <div style={{ height: '1px', background: '#111111' }} />
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* ════════════════════════════════════════
         SECTION 5: STATS BAR
         ════════════════════════════════════════ */}
      <div style={{
        display: 'flex',
        gap: '8px',
        padding: '24px 18px 8px',
        flexWrap: 'wrap',
        marginTop: '20px'
      }}>
        <div style={{
          background: '#0f0f0f',
          borderRadius: '10px',
          padding: '12px 10px',
          textAlign: 'center',
          flex: 1,
          minWidth: '100px'
        }}>
          <div style={{ fontSize: '20px', fontWeight: 800, color: '#c8860a' }}>{totalBooks}</div>
          <div style={{ fontSize: '10px', color: '#333333', marginTop: '2px', fontWeight: 600, letterSpacing: '0.5px' }}>
            كتاب
          </div>
        </div>

        <div style={{
          background: '#0f0f0f',
          borderRadius: '10px',
          padding: '12px 10px',
          textAlign: 'center',
          flex: 1,
          minWidth: '100px'
        }}>
          <div style={{ fontSize: '20px', fontWeight: 800, color: '#c8860a' }}>{localBooks}</div>
          <div style={{ fontSize: '10px', color: '#333333', marginTop: '2px', fontWeight: 600, letterSpacing: '0.5px' }}>
            محلي PDF
          </div>
        </div>

        <div style={{
          background: '#0f0f0f',
          borderRadius: '10px',
          padding: '12px 10px',
          textAlign: 'center',
          flex: 1,
          minWidth: '100px'
        }}>
          <div style={{ fontSize: '20px', fontWeight: 800, color: '#c8860a' }}>{onlineBooks}</div>
          <div style={{ fontSize: '10px', color: '#333333', marginTop: '2px', fontWeight: 600, letterSpacing: '0.5px' }}>
            أونلاين
          </div>
        </div>

        <div style={{
          background: '#0f0f0f',
          borderRadius: '10px',
          padding: '12px 10px',
          textAlign: 'center',
          flex: 1,
          minWidth: '100px'
        }}>
          <div style={{ fontSize: '20px', fontWeight: 800, color: '#c8860a' }}>{totalCategories}</div>
          <div style={{ fontSize: '10px', color: '#333333', marginTop: '2px', fontWeight: 600, letterSpacing: '0.5px' }}>
            أقسام
          </div>
        </div>
      </div>

      {/* RENDER BOOKREADER MODAL */}
      {showReader && selectedBook && (
        selectedBook.isLocal && selectedBook.pageFolder ? (
          <ImageReader
            book={selectedBook}
            readerVisible={readerVisible}
            onClose={handleCloseReader}
            onRate={(stars) => rateBook(selectedBook.id, stars)}
          />
        ) : (
          <BookReader
            book={selectedBook}
            onClose={() => {
              setSelectedBook(null);
              setShowReader(false);
            }}
          />
        )
      )}
    </div>
  );
}


