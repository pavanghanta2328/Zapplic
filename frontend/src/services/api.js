import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/api';

// ✅ Create axios instance with base configuration
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 300000, // 30 seconds timeout
  headers: {
    'Content-Type': 'application/json',
  },
});

// ✅ Request Interceptor - Attach token automatically
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');

    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// ✅ Response Interceptor - Handle token refresh and errors
api.interceptors.response.use(
  (response) => {
    return response;
  },
  async (error) => {
    const originalRequest = error.config;

    // Handle 401 Unauthorized - Token expired
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        const refreshToken = localStorage.getItem('refresh_token');

        if (refreshToken) {
          // Attempt to refresh the token
          const response = await axios.post(`${API_BASE_URL}/auth/refresh`, {
            refresh_token: refreshToken,
          });

          const { access_token, refresh_token: newRefreshToken } = response.data;

          // Store new tokens
          localStorage.setItem('access_token', access_token);
          if (newRefreshToken) {
            localStorage.setItem('refresh_token', newRefreshToken);
          }

          // Retry original request with new token
          originalRequest.headers.Authorization = `Bearer ${access_token}`;
          return api(originalRequest);
        }
      } catch (refreshError) {
        // Refresh failed - clear tokens and redirect to login
        localStorage.removeItem('access_token');
        localStorage.removeItem('refresh_token');
        window.location.href = '/login';
        return Promise.reject(refreshError);
      }
    }

    // Handle other errors
    return Promise.reject(error);
  }
);

// ==================== AUTH ENDPOINTS ====================

/**
 * Login with email and password
 * @param {string} email - User email
 * @param {string} password - User password
 * @returns {Promise} Response with tokens
 */
export const login = async (email, password) => {
  const response = await api.post('/auth/login', { email, password });
  return response.data;
};

/**
 * Register a new user
 * @param {object} userData - User registration data
 * @returns {Promise} Response with user data
 */
export const register = async (userData) => {
  const response = await api.post('/auth/register', userData);
  return response.data;
};

/**
 * Logout user (optional - clear tokens)
 */
export const logout = () => {
  localStorage.removeItem('access_token');
  localStorage.removeItem('refresh_token');
};

// ==================== RESUME ENDPOINTS ====================

/**
 * Upload a single resume file
 * @param {File} file - Resume file to upload
 * @returns {Promise} Response with parsed resume data
 */
export const uploadResume = async (file, employeeName = null) => {
  const formData = new FormData();
  formData.append('file', file);
  
  console.log('🔍 [uploadResume] employeeName:', employeeName);
  
  if (employeeName) {
    console.log('✅ [uploadResume] Appending employee_name:', employeeName);
    formData.append('employee_name', employeeName);
  } else {
    console.log('⚠️ [uploadResume] No employee_name to append');
  }

  const response = await api.post('/resumes/upload-with-action', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });

  return response.data;
};

/**
 * Get all resumes with pagination
 * @param {number} skip - Number of records to skip
 * @param {number} limit - Maximum number of records to return
 * @returns {Promise} Response with resumes array and total count
 */
export const getResumes = async (skip = 0, limit = 100) => {
  const response = await api.get(`/resumes?skip=${skip}&limit=${limit}`);
  return response.data;
};

/**
 * Get a single resume by ID
 * @param {string|number} id - Resume ID
 * @returns {Promise} Response with resume data
 */
export const getResume = async (id) => {
  const response = await api.get(`/resumes/${id}`);
  return response.data;
};

/**
 * Update resume data
 * @param {string|number} id - Resume ID
 * @param {object} data - Updated resume data
 * @returns {Promise} Response with updated resume
 */
export const updateResume = async (id, data) => {
  const response = await api.put(`/resumes/${id}`, data);
  return response.data;
};

/**
 * Delete a resume
 * @param {string|number} id - Resume ID
 * @returns {Promise} Response confirming deletion
 */
export const deleteResume = async (id) => {
  const response = await api.delete(`/resumes/${id}`);
  return response.data;
};

/**
 * Search resumes with filters
 * @param {string} query - Search query (keywords)
 * @param {string} location - Location filter
 * @param {string} skills - Skills filter
 * @param {number} skip - Number of records to skip
 * @param {number} limit - Maximum number of records to return
 * @returns {Promise} Response with filtered resumes
 */
export const searchResumes = async (query = '', location = '', skills = '', skip = 0, limit = 100) => {
  const params = new URLSearchParams();

  if (query) params.append('q', query);
  if (location) params.append('location', location);
  if (skills) params.append('skills', skills);
  params.append('skip', skip);
  params.append('limit', limit);

  const response = await api.get(`/resumes/search/?${params.toString()}`);
  return response.data;
};

/**
 * Bulk upload multiple resumes
 * @param {File[]} files - Array of resume files
 * @param {function} onProgress - Optional progress callback
 * @returns {Promise} Response with upload results
 */
// export const bulkUploadResumes = async (files, employeeName = null, onProgress) => {
//   const formData = new FormData();

//   files.forEach((file) => {
//     formData.append('files', file);
//   });


  // // If a single employeeName is provided, send it once so backend can map it
  // if (employeeName) {
  //   // send same employee name for each file so backend receives a list mapped by index
  //   for (let i = 0; i < files.length; i++) {
  //     formData.append('employee_names', employeeName);
  //   }
  // }
//   if (employeeName) {
//   files.forEach(() => {
//     formData.append("employee_names[]", employeeName);
//   });
// }

//   const config = {
//     headers: { 'Content-Type': 'multipart/form-data' },
//   };

//   if (onProgress) {
//     config.onUploadProgress = (progressEvent) => {
//       const percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total);
//       onProgress(percentCompleted);
//     };
//   }

//   const response = await api.post('/resumes/bulk-upload', formData, config);
//   return response.data;
// };

export const bulkUploadResumes = async (files, employeeName = null, onProgress) => {
  const formData = new FormData();

  // attach files
  files.forEach((file) => {
    formData.append("files", file);
  });

  // ⭐ send recruiter name once
  if (employeeName) {
    formData.append("employee_name", employeeName);
  }

  const config = {
    headers: { "Content-Type": "multipart/form-data" },
  };

  if (onProgress) {
    config.onUploadProgress = (progressEvent) => {
      const percentCompleted = Math.round(
        (progressEvent.loaded * 100) / progressEvent.total
      );
      onProgress(percentCompleted);
    };
  }

  const response = await api.post("/resumes/bulk-upload", formData, config);
  return response.data;
  
};

// ==================== USER ENDPOINTS ====================

/**
 * Get current user profile
 * @returns {Promise} Response with user data
 */
export const getCurrentUser = async () => {
  const response = await api.get('/users/me');
  return response.data;
};

/**
 * Update user profile
 * @param {object} userData - Updated user data
 * @returns {Promise} Response with updated user
 */
export const updateUserProfile = async (userData) => {
  const response = await api.put('/users/me', userData);
  return response.data;
};

// ==================== ANALYTICS ENDPOINTS (Optional) ====================

/**
 * Get resume statistics
 * @returns {Promise} Response with statistics
 */
export const getResumeStats = async () => {
  const response = await api.get('/resumes/stats');
  return response.data;
};

/**
 * Get parsing quality distribution
 * @returns {Promise} Response with quality metrics
 */
export const getParsingQuality = async () => {
  const response = await api.get('/resumes/quality-metrics');
  return response.data;
};

// ==================== HELPER FUNCTIONS ====================

/**
 * Check if user is authenticated
 * @returns {boolean} True if user has valid token
 */
export const isAuthenticated = () => {
  const token = localStorage.getItem('access_token');
  return !!token;
};

/**
 * Get authorization headers
 * @returns {object} Headers with Bearer token
 */
export const getAuthHeaders = () => {
  const token = localStorage.getItem('access_token');
  return {
    Authorization: `Bearer ${token}`,
  };
};

/**
 * Handle API errors consistently
 * @param {Error} error - Axios error object
 * @returns {string} User-friendly error message
 */
export const handleApiError = (error) => {
  if (error.response) {
    // Server responded with error
    const message = error.response.data?.detail || error.response.data?.message || 'An error occurred';
    return message;
  } else if (error.request) {
    // Request made but no response
    return 'Network error. Please check your connection.';
  } else {
    // Error in request setup
    return error.message || 'An unexpected error occurred';
  }
};

// Export the axios instance for custom requests
export default api;