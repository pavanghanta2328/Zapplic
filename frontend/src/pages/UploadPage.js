import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { FiUpload, FiFile, FiCheckCircle, FiAlertCircle, FiFileText } from 'react-icons/fi';
import { uploadResume } from '../services/api';

function UploadPage() {
  const navigate = useNavigate();
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);
  const [dragActive, setDragActive] = useState(false);
  const [associateOption, setAssociateOption] = useState('none');
  // const [employeeInput, setEmployeeInput] = useState('');
  const [selectedEmployee, setSelectedEmployee] = useState(null);
  const [employeeList, setEmployeeList] = useState([]);
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const [newEmployeeName, setNewEmployeeName] = useState('');

  // load persisted employee if present
  React.useEffect(() => {
    try {
      const saved = localStorage.getItem('zapplic_employee');
      if (saved) setSelectedEmployee(saved);
      const listRaw = localStorage.getItem('zapplic_employee_list');
      if (listRaw) setEmployeeList(JSON.parse(listRaw));
    } catch (e) {}
  }, []);

  const handleFileChange = (e) => {
    const selectedFile = e.target.files[0];
    validateAndSetFile(selectedFile);
  };

  const validateAndSetFile = (selectedFile) => {
    if (selectedFile) {
      // Validate file type
      const allowedTypes = ['application/pdf', 'application/msword', 
                           'application/vnd.openxmlformats-officedocument.wordprocessingml.document'];
      
      if (allowedTypes.includes(selectedFile.type)) {
        // Validate file size (10MB)
        if (selectedFile.size > 10 * 1024 * 1024) {
          setError('File size must be less than 10MB');
          setFile(null);
        } else {
          setFile(selectedFile);
          setError('');
        }
      } else {
        setError('Please upload a PDF or DOC/DOCX file');
        setFile(null);
      }
    }
  };

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      validateAndSetFile(e.dataTransfer.files[0]);
    }
  };

  const handleUpload = async () => {
    // Validation: require employee if that option chosen
    if (!file) {
      setError('Please select a file first');
      return;
    }
    if (associateOption === 'employee' && !selectedEmployee) {
      setError('Please add/select an employee before uploading');
      return;
    }

    setUploading(true);
    setError('');
    setSuccess(false);

    try {
      // Only pass employee name if "Employee" option is selected
      const empName = associateOption === 'employee' ? selectedEmployee : null;
      
      console.log('🔍 [UploadPage] handleUpload:');
      console.log('  associateOption:', associateOption);
      console.log('  selectedEmployee:', selectedEmployee);
      console.log('  empName (to send):', empName);
      
      const result = await uploadResume(file, empName);
      setSuccess(true);
      setFile(null);
      
      // Redirect to resume detail page after 2 seconds
      setTimeout(() => {
        navigate(`/resume/${result.id}`);
      }, 2000);
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to upload resume');
    } finally {
      setUploading(false);
    }
  };

  // const handleAddEmployee = () => {
  //   if (!employeeInput || employeeInput.trim() === '') return;
  //   const name = employeeInput.trim();
  //   setSelectedEmployee(name);
  //   try { localStorage.setItem('zapplic_employee', name); } catch (e) {}
  //   try {
  //     const curr = Array.isArray(employeeList) ? [...employeeList] : [];
  //     if (!curr.includes(name)) {
  //       curr.push(name);
  //       localStorage.setItem('zapplic_employee_list', JSON.stringify(curr));
  //       setEmployeeList(curr);
  //     }
  //   } catch (e) {}
  //   setEmployeeInput('');
  // };

  const handleSelectExisting = (val) => {
    if (!val) return;
    setSelectedEmployee(val);
    try { localStorage.setItem('zapplic_employee', val); } catch (e) {}
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50 py-8 px-4 sm:px-6 lg:px-8">
      {/* Animated Background Blobs */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-blue-200 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-blob"></div>
        <div className="absolute top-1/3 right-1/4 w-96 h-96 bg-purple-200 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-blob animation-delay-2000"></div>
        <div className="absolute bottom-1/4 left-1/2 w-96 h-96 bg-pink-200 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-blob animation-delay-4000"></div>
      </div>

      <div className="max-w-3xl mx-auto relative z-10">
        <div className="bg-white/80 backdrop-blur-lg rounded-2xl shadow-xl p-8 border border-white/20">
          {/* Header */}
          <div className="flex items-center gap-4 mb-8">
            <div className="p-3 bg-gradient-to-br from-blue-500 to-purple-600 rounded-2xl shadow-lg">
              <FiFileText className="text-white text-2xl" />
            </div>
            <div>
              <h2 className="text-3xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
                Upload Resume
              </h2>
              <p className="text-sm text-gray-600 mt-1">
                Upload a resume for automatic parsing and analysis
              </p>
            </div>
          </div>

          {/* File Upload Area */}
          <div 
            className={`border-2 border-dashed rounded-2xl p-12 text-center transition-all duration-300 ${
              dragActive 
                ? 'border-blue-500 bg-blue-50/50 scale-[1.02]' 
                : 'border-gray-300 hover:border-blue-400 hover:bg-blue-50/30'
            }`}
            onDragEnter={handleDrag}
            onDragLeave={handleDrag}
            onDragOver={handleDrag}
            onDrop={handleDrop}
          >
            <div className="inline-block p-6 bg-gradient-to-br from-blue-100 to-purple-100 rounded-full mb-6 transform transition-transform hover:scale-110">
              <FiUpload className="text-blue-600 text-4xl" />
            </div>
            
            <div>
              <label htmlFor="file-upload" className="cursor-pointer">
                <span className="block text-lg font-semibold text-gray-900 mb-2">
                  {file ? file.name : 'Choose a file or drag it here'}
                </span>
                <input
                  id="file-upload"
                  name="file-upload"
                  type="file"
                  className="sr-only"
                  accept=".pdf,.doc,.docx"
                  onChange={handleFileChange}
                />
              </label>
              <p className="text-sm text-gray-500 mb-4">
                PDF, DOC, or DOCX up to 10MB
              </p>
              
              {!file && (
                <button
                  onClick={() => document.getElementById('file-upload').click()}
                  className="inline-flex items-center gap-2 px-6 py-3 bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 text-white rounded-xl font-semibold shadow-lg hover:shadow-xl transition-all duration-300 transform hover:scale-105"
                >
                  <FiFile size={18} />
                  Browse Files
                </button>
              )}
            </div>

            {file && (
              <div className="mt-6 inline-flex items-center gap-3 px-6 py-3 bg-green-50 border-2 border-green-200 rounded-xl">
                <FiFile className="text-green-600" size={24} />
                <div className="text-left">
                  <p className="text-sm font-semibold text-green-800">{file.name}</p>
                  <p className="text-xs text-green-600">{(file.size / 1024).toFixed(2)} KB</p>
                </div>
                <button
                  onClick={() => setFile(null)}
                  className="ml-4 text-green-600 hover:text-green-800 font-semibold text-sm"
                >
                  Remove
                </button>
              </div>
            )}
          </div>

          {/* Error Message */}
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4 animate-shake">
              <div className="flex items-start">
                <FiAlertCircle className="text-red-500 text-xl mr-3 flex-shrink-0 mt-0.5" />
                <div className="flex-1">
                  <h3 className="text-red-800 font-semibold mb-1">Upload Failed</h3>
                  <p className="text-red-600 text-sm">
                    {typeof error === 'string' 
                      ? error 
                      : error?.message || error?.msg || error?.detail || JSON.stringify(error)
                    }
                  </p>
                </div>
              </div>
            </div>
          )}

          {/* Success Message */}
          {success && (
            <div className="mt-6 p-4 bg-green-50 border-l-4 border-green-500 rounded-xl shadow-lg animate-slideIn">
              <div className="flex items-center gap-3">
                <FiCheckCircle className="text-green-500 flex-shrink-0" size={24} />
                <p className="text-sm font-medium text-green-800">
                  Resume uploaded successfully! Redirecting...
                </p>
              </div>
            </div>
          )}

          {/* Upload Button */}
          {/* Associate Employee (optional) */}
          <div className="mt-6 grid grid-cols-1 gap-3">
            <label className="text-sm font-medium text-gray-700">Associate resume with</label>
            <div className="flex items-center gap-3">
              <select
                value={associateOption}
                onChange={(e) => setAssociateOption(e.target.value)}
                className="px-3 py-2 border rounded-lg"
              >
                <option value="none">None</option>
                <option value="employee">Employee</option>
              </select>
{associateOption === 'employee' && (
  <div className="relative w-72">

    {/* Dropdown Trigger */}
    <div
      onClick={() => setDropdownOpen(!dropdownOpen)}
      className="px-4 py-2.5 bg-white border border-gray-300 rounded-xl shadow-sm cursor-pointer flex justify-between items-center hover:border-blue-500 transition"
    >
      <span className={`${selectedEmployee ? 'text-gray-900' : 'text-gray-400'}`}>
        {selectedEmployee || 'Select employee'}
      </span>
      <span className="text-gray-500 text-sm">▾</span>
    </div>

    {/* Dropdown Menu */}
    {dropdownOpen && (
      <div className="absolute mt-2 w-full bg-white border border-gray-200 rounded-2xl shadow-2xl z-50 overflow-hidden animate-fadeIn">

        {/* Add Section */}
        <div className="p-4 border-b bg-gray-50">
          <p className="text-xs font-semibold text-gray-500 mb-2 uppercase tracking-wide">
            Add New Employee
          </p>

          <div className="flex gap-2">
            <input
              type="text"
              placeholder="Type employee name..."
              value={newEmployeeName}
              onChange={(e) => setNewEmployeeName(e.target.value)}
              className="flex-1 px-3 py-2 text-sm border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:outline-none"
            />
            <button
              onClick={() => {
                const name = newEmployeeName.trim();
                if (!name) return;

                if (!employeeList.includes(name)) {
                  const updated = [...employeeList, name];
                  setEmployeeList(updated);
                  localStorage.setItem('zapplic_employee_list', JSON.stringify(updated));
                }

                setSelectedEmployee(name);
                localStorage.setItem('zapplic_employee', name);
                setNewEmployeeName('');
                setDropdownOpen(false);
              }}
              className="px-3 py-2 text-sm bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition"
            >
              Add
            </button>
          </div>
        </div>

        {/* Employee List */}
        <div className="max-h-48 overflow-y-auto">
          {employeeList.length === 0 && (
            <div className="px-4 py-3 text-sm text-gray-400 text-center">
              No employees yet
            </div>
          )}

          {employeeList.map((emp, index) => (
            <div
              key={index}
              className={`flex items-center justify-between px-4 py-2.5 text-sm cursor-pointer transition
                ${selectedEmployee === emp
                  ? 'bg-blue-50 text-blue-700 font-medium'
                  : 'hover:bg-gray-100 text-gray-700'
                }`}
            >
              <span
                onClick={() => {
                  setSelectedEmployee(emp);
                  localStorage.setItem('zapplic_employee', emp);
                  setDropdownOpen(false);
                }}
                className="flex-1"
              >
                {emp}
              </span>

              <button
                onClick={() => {
                  const updated = employeeList.filter(e => e !== emp);
                  setEmployeeList(updated);
                  localStorage.setItem('zapplic_employee_list', JSON.stringify(updated));

                  if (selectedEmployee === emp) {
                    setSelectedEmployee(null);
                    localStorage.removeItem('zapplic_employee');
                  }
                }}
                className="text-gray-400 hover:text-red-500 transition ml-2"
              >
                ✕
              </button>
            </div>
          ))}
        </div>

      </div>
    )}
  </div>
)}
  



                  {/* <input
                    type="text"
                    placeholder="Or type new employee name"
                    value={employeeInput}
                    onChange={(e) => setEmployeeInput(e.target.value)}
                    className="px-3 py-2 border rounded-lg"
                  />
                  <button
                    onClick={handleAddEmployee}
                    className="px-4 py-2 bg-blue-600 text-white rounded-lg"
                  >
                    Add
                  </button> */}
                {/* </div>
              )} */}

              {/* {selectedEmployee && (
                <div className="ml-4 inline-flex items-center gap-2 bg-green-50 border border-green-200 px-3 py-1 rounded-full">
                  <span className="text-sm text-green-800">{selectedEmployee}</span>
                  <button onClick={() => { setSelectedEmployee(null); try{ localStorage.removeItem('zapplic_employee'); }catch(e){} }} className="text-green-600 font-semibold">Remove</button>
                </div>
              )} */}
            </div>
          </div>

          <div className="mt-8">
            <button
              onClick={handleUpload}
              disabled={!file || uploading || (associateOption === 'employee' && !selectedEmployee)}
              className={`w-full flex justify-center items-center gap-2 py-3.5 rounded-xl font-semibold text-white transition-all duration-300 transform ${
                !file || uploading
                  ? 'bg-gray-400 cursor-not-allowed'
                  : 'bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 hover:scale-[1.02] hover:shadow-lg active:scale-[0.98]'
              }`}
            >
              {uploading ? (
                <>
                  <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                  </svg>
                  <span>Uploading & Parsing...</span>
                </>
              ) : (
                <>
                  <FiUpload size={20} />
                  <span>Upload Resume</span>
                </>
              )}
            </button>
          </div>

          {/* Instructions */}
          <div className="mt-8 bg-blue-50/80 backdrop-blur-lg rounded-2xl p-6 border border-blue-200/50">
            <h3 className="text-sm font-bold text-blue-800 mb-3 flex items-center gap-2">
              <span className="text-lg">📋</span>
              Upload Instructions
            </h3>
            <ul className="text-sm text-blue-700 space-y-2">
              <li className="flex items-start gap-2">
                <span className="text-blue-500 mt-0.5">•</span>
                <span>Supported formats: PDF, DOC, and DOCX files</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-blue-500 mt-0.5">•</span>
                <span>Maximum file size: 10MB per resume</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-blue-500 mt-0.5">•</span>
                <span>Resume will be automatically parsed using AI technology</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-blue-500 mt-0.5">•</span>
                <span>You can review and edit the parsed data after upload</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-blue-500 mt-0.5">•</span>
                <span>Drag and drop files or click to browse your computer</span>
              </li>
            </ul>
          </div>

          {/* Quick Actions */}
          <div className="mt-6 flex flex-col sm:flex-row gap-3">
            <button
              onClick={() => navigate('/dashboard')}
              className="flex-1 px-6 py-3 border-2 border-gray-300 rounded-xl font-semibold text-gray-700 hover:bg-gray-50 hover:border-gray-400 transition-all duration-200 transform hover:scale-[1.02]"
            >
              View All Resumes
            </button>
            <button
              onClick={() => navigate('/bulk-upload')}
              className="flex-1 px-6 py-3 border-2 border-blue-300 rounded-xl font-semibold text-blue-600 hover:bg-blue-50 hover:border-blue-400 transition-all duration-200 transform hover:scale-[1.02]"
            >
              Bulk Upload
            </button>
          </div>
        </div>
      </div>

      {/* Add custom animations */}
      <style>{`
        @keyframes blob {
          0% { transform: translate(0px, 0px) scale(1); }
          33% { transform: translate(30px, -50px) scale(1.1); }
          66% { transform: translate(-20px, 20px) scale(0.9); }
          100% { transform: translate(0px, 0px) scale(1); }
        }
        .animate-blob {
          animation: blob 7s infinite;
        }
        .animation-delay-2000 {
          animation-delay: 2s;
        }
        .animation-delay-4000 {
          animation-delay: 4s;
        }
        @keyframes shake {
          0%, 100% { transform: translateX(0); }
          25% { transform: translateX(-10px); }
          75% { transform: translateX(10px); }
        }
        .animate-shake {
          animation: shake 0.3s ease-in-out;
        }
        @keyframes slideIn {
          from {
            opacity: 0;
            transform: translateY(-10px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
        .animate-slideIn {
          animation: slideIn 0.3s ease-out;
        }
      `}</style>
    </div>
  );
}

export default UploadPage;