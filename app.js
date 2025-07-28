// Connecting the Dots - PDF Outline Extractor
// Enhanced responsive application with robust file handling

// Sample outline data for demo mode
const SAMPLE_OUTLINE = {
  "title": "Understanding Artificial Intelligence: A Comprehensive Guide",
  "outline": [
    {"level": "H1", "text": "Introduction to AI", "page": 1},
    {"level": "H2", "text": "What is Artificial Intelligence?", "page": 2},
    {"level": "H3", "text": "Brief History of AI", "page": 3},
    {"level": "H3", "text": "AI vs Machine Learning vs Deep Learning", "page": 5},
    {"level": "H1", "text": "Core AI Technologies", "page": 7},
    {"level": "H2", "text": "Machine Learning Fundamentals", "page": 8},
    {"level": "H3", "text": "Supervised Learning", "page": 9},
    {"level": "H3", "text": "Unsupervised Learning", "page": 11},
    {"level": "H3", "text": "Reinforcement Learning", "page": 13},
    {"level": "H2", "text": "Deep Learning and Neural Networks", "page": 15},
    {"level": "H3", "text": "Convolutional Neural Networks", "page": 17},
    {"level": "H3", "text": "Recurrent Neural Networks", "page": 19},
    {"level": "H1", "text": "AI Applications", "page": 21},
    {"level": "H2", "text": "Natural Language Processing", "page": 22},
    {"level": "H2", "text": "Computer Vision", "page": 24},
    {"level": "H2", "text": "Robotics and Automation", "page": 26},
    {"level": "H1", "text": "Future of AI", "page": 28},
    {"level": "H2", "text": "Emerging Trends", "page": 29},
    {"level": "H2", "text": "Ethical Considerations", "page": 31}
  ]
};

// Application state
let currentFile = null;
let currentOutlineData = null;
let activeOutlineItem = null;

// DOM elements
let uploadView, outlineView;
let dropZone, fileInput, browseBtn, filePreview, fileName, fileSize, removeFileBtn;
let progressContainer, progressFill, progressPercentage, progressText, processBtn;
let backBtn, downloadJsonBtn, documentTitle, documentSubtitle;
let outlineTree, previewContent, pageCounter;
let expandAllBtn, collapseAllBtn, demoBtn;

// Initialize application
document.addEventListener('DOMContentLoaded', function() {
  initializeElements();
  initializeEventListeners();
  resetToUploadView();
});

function initializeElements() {
  // Views
  uploadView = document.getElementById('upload-view');
  outlineView = document.getElementById('outline-view');
  
  // Upload elements
  dropZone = document.getElementById('drop-zone');
  fileInput = document.getElementById('file-input');
  browseBtn = dropZone.querySelector('.browse-btn');
  filePreview = document.getElementById('file-preview');
  fileName = document.getElementById('file-name');
  fileSize = document.getElementById('file-size');
  removeFileBtn = document.getElementById('remove-file');
  progressContainer = document.getElementById('progress-container');
  progressFill = document.getElementById('progress-fill');
  progressPercentage = document.getElementById('progress-percentage');
  progressText = document.getElementById('progress-text');
  processBtn = document.getElementById('process-btn');
  demoBtn = document.getElementById('demo-btn');
  
  // Outline elements
  backBtn = document.getElementById('back-btn');
  downloadJsonBtn = document.getElementById('download-json-btn');
  documentTitle = document.getElementById('document-title');
  documentSubtitle = document.getElementById('document-subtitle');
  outlineTree = document.getElementById('outline-tree');
  previewContent = document.getElementById('preview-content');
  pageCounter = document.getElementById('page-counter');
  expandAllBtn = document.getElementById('expand-all');
  collapseAllBtn = document.getElementById('collapse-all');
}

function initializeEventListeners() {
  // File input events
  fileInput.addEventListener('change', handleFileSelect);
  browseBtn.addEventListener('click', (e) => {
    e.preventDefault();
    e.stopPropagation();
    fileInput.click();
  });
  
  // Drag and drop events
  dropZone.addEventListener('dragover', handleDragOver);
  dropZone.addEventListener('dragleave', handleDragLeave);
  dropZone.addEventListener('drop', handleDrop);
  dropZone.addEventListener('click', handleDropZoneClick);
  
  // File management
  removeFileBtn.addEventListener('click', removeSelectedFile);
  processBtn.addEventListener('click', startProcessing);
  
  // Navigation
  backBtn.addEventListener('click', resetToUploadView);
  demoBtn.addEventListener('click', loadDemoMode);
  
  // Outline controls
  expandAllBtn.addEventListener('click', expandAllOutlineItems);
  collapseAllBtn.addEventListener('click', collapseAllOutlineItems);
  downloadJsonBtn.addEventListener('click', downloadJSON);
  
  // Prevent default drag behaviors on document
  document.addEventListener('dragover', (e) => e.preventDefault());
  document.addEventListener('drop', (e) => e.preventDefault());
  
  // Keyboard navigation
  document.addEventListener('keydown', handleKeyboardNavigation);
}

// File handling functions
function handleDragOver(e) {
  e.preventDefault();
  e.stopPropagation();
  dropZone.classList.add('drag-over');
}

function handleDragLeave(e) {
  e.preventDefault();
  e.stopPropagation();
  if (!dropZone.contains(e.relatedTarget)) {
    dropZone.classList.remove('drag-over');
  }
}

function handleDrop(e) {
  e.preventDefault();
  e.stopPropagation();
  dropZone.classList.remove('drag-over');
  
  const files = e.dataTransfer.files;
  if (files.length > 0) {
    handleFile(files[0]);
  }
}

function handleDropZoneClick(e) {
  if (e.target === dropZone || dropZone.contains(e.target)) {
    if (!currentFile) {
      fileInput.click();
    }
  }
}

function handleFileSelect(e) {
  const file = e.target.files[0];
  if (file) {
    handleFile(file);
  }
}

function handleFile(file) {
  if (!validateFile(file)) {
    return;
  }
  
  currentFile = file;
  displayFilePreview(file);
  showProcessButton();
}

function validateFile(file) {
  // Check file type
  const validTypes = ['application/pdf'];
  const validExtensions = ['.pdf'];
  const isValidType = validTypes.includes(file.type) || 
                     validExtensions.some(ext => file.name.toLowerCase().endsWith(ext));
  
  if (!isValidType) {
    showError('Please select a PDF file.');
    return false;
  }
  
  // Check file size (50MB limit)
  const maxSize = 50 * 1024 * 1024;
  if (file.size > maxSize) {
    showError('File size too large. Please select a file smaller than 50MB.');
    return false;
  }
  
  return true;
}

function displayFilePreview(file) {
  fileName.textContent = file.name;
  fileSize.textContent = formatFileSize(file.size);
  filePreview.classList.remove('hidden');
  dropZone.style.display = 'none';
}

function removeSelectedFile() {
  currentFile = null;
  fileInput.value = '';
  filePreview.classList.add('hidden');
  dropZone.style.display = 'flex';
  hideProcessButton();
}

function showProcessButton() {
  processBtn.classList.remove('hidden');
}

function hideProcessButton() {
  processBtn.classList.add('hidden');
}

function formatFileSize(bytes) {
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  if (bytes === 0) return '0 Bytes';
  const i = Math.floor(Math.log(bytes) / Math.log(1024));
  return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i];
}

function showError(message) {
  alert(message); // In a real app, you'd use a proper toast/notification system
}

// Processing functions
function startProcessing() {
  if (!currentFile) {
    showError('Please select a file first.');
    return;
  }
  
  // Hide file preview and process button
  filePreview.classList.add('hidden');
  processBtn.classList.add('hidden');
  
  // Show progress
  progressContainer.classList.remove('hidden');
  
  // Simulate processing with realistic progress
  simulateProcessing();
}

function simulateProcessing() {
  let progress = 0;
  const steps = [
    { progress: 15, text: 'Reading PDF file...', duration: 300 },
    { progress: 35, text: 'Analyzing document structure...', duration: 500 },
    { progress: 60, text: 'Extracting headings and hierarchy...', duration: 400 },
    { progress: 80, text: 'Mapping page numbers...', duration: 300 },
    { progress: 95, text: 'Generating outline structure...', duration: 200 },
    { progress: 100, text: 'Complete!', duration: 200 }
  ];
  
  let stepIndex = 0;
  
  function processStep() {
    if (stepIndex >= steps.length) {
      setTimeout(() => {
        showOutlineView();
      }, 300);
      return;
    }
    
    const step = steps[stepIndex];
    progressFill.style.width = step.progress + '%';
    progressPercentage.textContent = step.progress + '%';
    progressText.textContent = step.text;
    
    stepIndex++;
    setTimeout(processStep, step.duration);
  }
  
  processStep();
}

// Demo mode
function loadDemoMode() {
  currentFile = { name: 'sample-ai-guide.pdf', type: 'application/pdf', size: 2457600 };
  currentOutlineData = SAMPLE_OUTLINE;
  startProcessing();
}

// View management
function resetToUploadView() {
  uploadView.classList.add('active');
  outlineView.classList.remove('active');
  
  // Reset state
  currentFile = null;
  currentOutlineData = null;
  activeOutlineItem = null;
  
  // Reset UI - completely clear everything
  fileInput.value = '';
  filePreview.classList.add('hidden');
  progressContainer.classList.add('hidden');
  processBtn.classList.add('hidden');
  dropZone.style.display = 'flex';
  progressFill.style.width = '0%';
  progressPercentage.textContent = '0%';
  progressText.textContent = 'Analyzing document structure';
  
  // Clear outline tree completely
  outlineTree.innerHTML = '';
  
  // Reset preview content
  previewContent.innerHTML = `
    <div class="preview-placeholder">
      <svg width="64" height="64" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/>
        <polyline points="14,2 14,8 20,8"/>
      </svg>
      <h3>Select an outline item</h3>
      <p>Click on any heading in the outline to view its page information</p>
    </div>
  `;
  
  // Reset page counter
  pageCounter.textContent = 'Page - of -';
  
  // Remove any lingering feedback elements
  const existingFeedback = document.querySelectorAll('.download-feedback');
  existingFeedback.forEach(el => el.remove());
}

function showOutlineView() {
  uploadView.classList.remove('active');
  outlineView.classList.add('active');
  
  // Use sample data for demo
  if (!currentOutlineData) {
    currentOutlineData = SAMPLE_OUTLINE;
  }
  
  // Update document info
  documentTitle.textContent = currentOutlineData.title;
  documentSubtitle.textContent = `${currentOutlineData.outline.length} sections found`;
  
  // Populate outline
  populateOutline();
  
  // Update page counter
  const totalPages = Math.max(...currentOutlineData.outline.map(item => item.page));
  pageCounter.textContent = `Page - of ${totalPages}`;
}

// Outline rendering
function populateOutline() {
  const outline = currentOutlineData.outline;
  const tree = buildOutlineTree(outline);
  outlineTree.innerHTML = '';
  outlineTree.appendChild(renderOutlineTree(tree));
}

function buildOutlineTree(outline) {
  const tree = [];
  const stack = [];
  
  outline.forEach((item, index) => {
    const node = { ...item, index, children: [] };
    
    // Find parent based on heading level hierarchy
    while (stack.length > 0) {
      const parent = stack[stack.length - 1];
      if (shouldBeChild(node.level, parent.level)) {
        parent.children.push(node);
        stack.push(node);
        return;
      } else {
        stack.pop();
      }
    }
    
    // No suitable parent found, add to root
    tree.push(node);
    stack.push(node);
  });
  
  return tree;
}

function shouldBeChild(childLevel, parentLevel) {
  const levelOrder = ['title', 'H1', 'H2', 'H3'];
  const childIndex = levelOrder.indexOf(childLevel);
  const parentIndex = levelOrder.indexOf(parentLevel);
  return childIndex > parentIndex;
}

function renderOutlineTree(tree) {
  const ul = document.createElement('ul');
  
  tree.forEach(node => {
    const li = document.createElement('li');
    
    if (node.children.length > 0) {
      const details = document.createElement('details');
      details.open = true; // Open by default
      details.classList.add('outline-group');
      
      const summary = document.createElement('summary');
      summary.innerHTML = `
        <span class="toggle-indicator">▶</span>
        <a href="#" class="outline-anchor level-${node.level.toLowerCase()}" 
           data-page="${node.page}" data-index="${node.index}">
          ${node.text} <small>(Page ${node.page})</small>
        </a>
      `;
      
      details.appendChild(summary);
      details.appendChild(renderOutlineTree(node.children));
      li.appendChild(details);
    } else {
      li.innerHTML = `
        <a href="#" class="outline-anchor level-${node.level.toLowerCase()}" 
           data-page="${node.page}" data-index="${node.index}">
          ${node.text} <small>(Page ${node.page})</small>
        </a>
      `;
    }
    
    ul.appendChild(li);
  });
  
  // Add click listeners to all outline anchors
  ul.addEventListener('click', (e) => {
    if (e.target.classList.contains('outline-anchor')) {
      e.preventDefault();
      const page = parseInt(e.target.dataset.page);
      const index = parseInt(e.target.dataset.index);
      const item = currentOutlineData.outline[index];
      handleOutlineClick(e.target, item);
    }
  });
  
  return ul;
}

function handleOutlineClick(element, item) {
  // Remove active class from previous item
  if (activeOutlineItem) {
    activeOutlineItem.classList.remove('active');
  }
  
  // Add active class to clicked item
  element.classList.add('active');
  activeOutlineItem = element;
  
  // Update preview and page counter
  updatePreviewPanel(item);
  pageCounter.textContent = `Page ${item.page} of ${Math.max(...currentOutlineData.outline.map(i => i.page))}`;
}

function updatePreviewPanel(item) {
  previewContent.innerHTML = `
    <div class="page-info">
      <h3>${item.text}</h3>
      <p><strong>Level:</strong> ${item.level}</p>
      <p><strong>Page:</strong> ${item.page}</p>
      <div style="margin-top: var(--space-16); padding: var(--space-16); background-color: var(--color-bg-7); border-radius: var(--radius-base); font-size: var(--font-size-sm); color: var(--color-text-secondary);">
        <p><strong>Note:</strong> In a full implementation, this panel would display the actual PDF page content for this section.</p>
        <p>Current selection: <em>${item.text}</em> (${item.level})</p>
      </div>
    </div>
  `;
}

// Outline controls
function expandAllOutlineItems() {
  const details = outlineTree.querySelectorAll('details');
  details.forEach(detail => {
    detail.open = true;
  });
  
  // Visual feedback
  expandAllBtn.style.backgroundColor = 'var(--color-primary)';
  expandAllBtn.style.color = 'var(--color-btn-primary-text)';
  setTimeout(() => {
    expandAllBtn.style.backgroundColor = '';
    expandAllBtn.style.color = '';
  }, 200);
}

function collapseAllOutlineItems() {
  const details = outlineTree.querySelectorAll('details');
  details.forEach(detail => {
    detail.open = false;
  });
  
  // Visual feedback
  collapseAllBtn.style.backgroundColor = 'var(--color-primary)';
  collapseAllBtn.style.color = 'var(--color-btn-primary-text)';
  setTimeout(() => {
    collapseAllBtn.style.backgroundColor = '';
    collapseAllBtn.style.color = '';
  }, 200);
}

// JSON download with feedback
function downloadJSON() {
  if (!currentOutlineData) {
    showError('No outline data available to download.');
    return;
  }
  
  const dataStr = JSON.stringify(currentOutlineData, null, 2);
  const dataBlob = new Blob([dataStr], { type: 'application/json' });
  const url = URL.createObjectURL(dataBlob);
  
  const link = document.createElement('a');
  link.href = url;
  link.download = `${currentOutlineData.title.replace(/[^a-z0-9]/gi, '_').toLowerCase()}_outline.json`;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
  
  // Show download feedback
  showDownloadFeedback();
}

function showDownloadFeedback() {
  // Remove any existing feedback
  const existingFeedback = document.querySelectorAll('.download-feedback');
  existingFeedback.forEach(el => el.remove());
  
  // Create feedback element
  const feedback = document.createElement('div');
  feedback.className = 'download-feedback';
  feedback.innerHTML = `
    <div style="display: flex; align-items: center; gap: var(--space-8);">
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M20 6L9 17l-5-5"/>
      </svg>
      JSON file downloaded successfully!
    </div>
  `;
  
  document.body.appendChild(feedback);
  
  // Show feedback
  setTimeout(() => feedback.classList.add('show'), 100);
  
  // Hide feedback after 3 seconds
  setTimeout(() => {
    feedback.classList.remove('show');
    setTimeout(() => feedback.remove(), 300);
  }, 3000);
}

// Keyboard navigation
function handleKeyboardNavigation(e) {
  if (!outlineView.classList.contains('active')) return;
  
  const outlineAnchors = Array.from(outlineTree.querySelectorAll('.outline-anchor'));
  if (outlineAnchors.length === 0) return;
  
  const currentIndex = activeOutlineItem ? 
    outlineAnchors.indexOf(activeOutlineItem) : -1;
  
  let nextIndex = currentIndex;
  
  switch (e.key) {
    case 'ArrowDown':
      e.preventDefault();
      nextIndex = Math.min(currentIndex + 1, outlineAnchors.length - 1);
      break;
    case 'ArrowUp':
      e.preventDefault();
      nextIndex = Math.max(currentIndex - 1, 0);
      break;
    case 'Home':
      e.preventDefault();
      nextIndex = 0;
      break;
    case 'End':
      e.preventDefault();
      nextIndex = outlineAnchors.length - 1;
      break;
    default:
      return;
  }
  
  if (nextIndex !== currentIndex && nextIndex >= 0) {
    const nextElement = outlineAnchors[nextIndex];
    nextElement.click();
    nextElement.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
  }
}