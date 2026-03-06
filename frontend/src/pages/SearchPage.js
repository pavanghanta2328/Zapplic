import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { FiSearch, FiEye, FiEdit, FiMapPin, FiCode, FiUser, FiMail, FiPhone, FiFileText } from 'react-icons/fi';
import { searchResumes } from '../services/api';

function SearchPage() {
  const navigate = useNavigate();
  const [query, setQuery] = useState('');
  const [location, setLocation] = useState('');
  const [skills, setSkills] = useState('');
  const [results, setResults] = useState([]);
  const [searching, setSearching] = useState(false);
  const [searched, setSearched] = useState(false);
  const [total, setTotal] = useState(0);
  const [focusedField, setFocusedField] = useState(null);

  const handleSearch = async (e) => {
    e.preventDefault();
    
    if (!query && !location && !skills) {
      alert('Please enter at least one search criteria');
      return;
    }

    setSearching(true);
    setSearched(false);

    try {
      const data = await searchResumes(query, location, skills);
      setResults(data.resumes);
      setTotal(data.total);
      setSearched(true);
    } catch (err) {
      console.error('Search failed:', err);
      alert('Search failed. Please try again.');
    } finally {
      setSearching(false);
    }
  };

  const handleClear = () => {
    setQuery('');
    setLocation('');
    setSkills('');
    setResults([]);
    setSearched(false);
    setTotal(0);
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50 py-8 px-4 sm:px-6 lg:px-8">
      {/* Animated Background Blobs */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-blue-200 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-blob"></div>
        <div className="absolute top-1/3 right-1/4 w-96 h-96 bg-purple-200 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-blob animation-delay-2000"></div>
        <div className="absolute bottom-1/4 left-1/2 w-96 h-96 bg-pink-200 rounded-full mix-blend-multiply filter blur-3xl opacity-20 animate-blob animation-delay-4000"></div>
      </div>

      <div className="max-w-6xl mx-auto relative z-10">
        {/* Search Form */}
        <div className="bg-white/80 backdrop-blur-lg rounded-2xl shadow-xl p-8 border border-white/20 mb-6">
          <div className="flex items-center gap-4 mb-6">
            <div className="p-3 bg-gradient-to-br from-blue-500 to-purple-600 rounded-2xl shadow-lg">
              <FiSearch className="text-white text-2xl" />
            </div>
            <div>
              <h2 className="text-3xl font-bold bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">
                Search Resumes
              </h2>
              <p className="text-sm text-gray-600 mt-1">
                Find candidates by keywords, location, or skills
              </p>
            </div>
          </div>
          
          <form onSubmit={handleSearch}>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
              {/* Keyword Search */}
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">
                  Keyword
                </label>
                <div className="relative">
                  <div className={`absolute left-4 top-1/2 transform -translate-y-1/2 transition-colors ${
                    focusedField === 'query' ? 'text-blue-600' : 'text-gray-400'
                  }`}>
                    <FiUser size={20} />
                  </div>
                  <input
                    type="text"
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    onFocus={() => setFocusedField('query')}
                    onBlur={() => setFocusedField(null)}
                    className="w-full pl-12 pr-4 py-3 border-2 border-gray-200 rounded-xl focus:border-blue-500 focus:ring-4 focus:ring-blue-100 outline-none transition-all duration-200 bg-white/50"
                    placeholder="e.g., Python, Java, React"
                  />
                </div>
              </div>

              {/* Location Filter */}
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">
                  Location
                </label>
                <div className="relative">
                  <div className={`absolute left-4 top-1/2 transform -translate-y-1/2 transition-colors ${
                    focusedField === 'location' ? 'text-blue-600' : 'text-gray-400'
                  }`}>
                    <FiMapPin size={20} />
                  </div>
                  <input
                    type="text"
                    value={location}
                    onChange={(e) => setLocation(e.target.value)}
                    onFocus={() => setFocusedField('location')}
                    onBlur={() => setFocusedField(null)}
                    className="w-full pl-12 pr-4 py-3 border-2 border-gray-200 rounded-xl focus:border-blue-500 focus:ring-4 focus:ring-blue-100 outline-none transition-all duration-200 bg-white/50"
                    placeholder="e.g., Bangalore, Hyderabad"
                  />
                </div>
              </div>

              {/* Skills Filter */}
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">
                  Skills
                </label>
                <div className="relative">
                  <div className={`absolute left-4 top-1/2 transform -translate-y-1/2 transition-colors ${
                    focusedField === 'skills' ? 'text-blue-600' : 'text-gray-400'
                  }`}>
                    <FiCode size={20} />
                  </div>
                  <input
                    type="text"
                    value={skills}
                    onChange={(e) => setSkills(e.target.value)}
                    onFocus={() => setFocusedField('skills')}
                    onBlur={() => setFocusedField(null)}
                    className="w-full pl-12 pr-4 py-3 border-2 border-gray-200 rounded-xl focus:border-blue-500 focus:ring-4 focus:ring-blue-100 outline-none transition-all duration-200 bg-white/50"
                    placeholder="e.g., FastAPI, SQL"
                  />
                </div>
              </div>
            </div>

            {/* Search Buttons */}
            <div className="flex flex-col sm:flex-row gap-3">
              <button
                type="submit"
                disabled={searching}
                className={`flex items-center justify-center gap-2 px-6 py-3 rounded-xl font-semibold text-white transition-all duration-300 transform ${
                  searching
                    ? 'bg-gray-400 cursor-not-allowed'
                    : 'bg-gradient-to-r from-blue-600 to-purple-600 hover:from-blue-700 hover:to-purple-700 hover:scale-[1.02] hover:shadow-lg active:scale-[0.98]'
                }`}
              >
                {searching ? (
                  <>
                    <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                    </svg>
                    Searching...
                  </>
                ) : (
                  <>
                    <FiSearch size={18} />
                    Search Resumes
                  </>
                )}
              </button>
              
              <button
                type="button"
                onClick={handleClear}
                className="px-6 py-3 border-2 border-gray-300 rounded-xl font-semibold text-gray-700 hover:bg-gray-50 hover:border-gray-400 transition-all duration-200 transform hover:scale-[1.02] active:scale-[0.98]"
              >
                Clear Filters
              </button>
            </div>
          </form>
        </div>

        {/* Search Results */}
        {searched && (
          <div className="bg-white/80 backdrop-blur-lg rounded-2xl shadow-xl border border-white/20 overflow-hidden">
            <div className="px-6 py-4 bg-gradient-to-r from-gray-50 to-gray-100/80 border-b border-gray-200/50">
              <div className="flex items-center justify-between">
                <h3 className="text-xl font-bold text-gray-900 flex items-center gap-2">
                  <FiFileText className="text-blue-600" />
                  Search Results
                </h3>
                <span className="px-4 py-2 bg-gradient-to-r from-blue-100 to-purple-100 rounded-full text-sm font-semibold text-gray-700">
                  {total} {total === 1 ? 'Result' : 'Results'} Found
                </span>
              </div>
            </div>

            {results.length === 0 ? (
              <div className="px-6 py-16 text-center">
                <div className="inline-block p-6 bg-gray-100 rounded-full mb-6">
                  <FiSearch className="text-gray-400 text-5xl" />
                </div>
                <h3 className="text-2xl font-bold text-gray-800 mb-3">No Results Found</h3>
                <p className="text-gray-600 mb-6 max-w-md mx-auto">
                  We couldn't find any resumes matching your search criteria. Try adjusting your filters.
                </p>
                <button
                  onClick={handleClear}
                  className="text-blue-600 hover:text-blue-800 font-semibold"
                >
                  Clear Search
                </button>
              </div>
            ) : (
              <div className="divide-y divide-gray-200/50">
                {results.map((resume, index) => (
                  <div 
                    key={resume.id} 
                    className="px-6 py-6 hover:bg-blue-50/50 transition-all duration-200 group"
                    style={{ animationDelay: `${index * 50}ms` }}
                  >
                    <div className="flex flex-col lg:flex-row lg:items-start lg:justify-between gap-4">
                      <div className="flex-1">
                        <div className="flex items-center gap-3 mb-3">
                          <div className="flex-shrink-0 h-12 w-12 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center text-white font-bold text-lg shadow-lg">
                            {resume.name ? resume.name.charAt(0).toUpperCase() : '?'}
                          </div>
                          <div>
                            <h4 className="text-xl font-semibold text-gray-900 group-hover:text-blue-600 transition-colors">
                              {resume.name || 'N/A'}
                            </h4>
                            <p className="text-sm text-gray-500">
                              {resume.original_filename || 'Resume'}
                            </p>
                          </div>
                        </div>

                        <div className="space-y-2 ml-0 lg:ml-15">
                          {resume.email && (
                            <div className="flex items-center text-sm text-gray-700">
                              <FiMail className="mr-2 text-blue-500" size={16} />
                              <span className="truncate">{resume.email}</span>
                            </div>
                          )}
                          {resume.mobile_number && (
                            <div className="flex items-center text-sm text-gray-700">
                              <FiPhone className="mr-2 text-green-500" size={16} />
                              {resume.mobile_number}
                            </div>
                          )}
                          {resume.location && (
                            <div className="flex items-center text-sm text-gray-700">
                              <FiMapPin className="mr-2 text-purple-500" size={16} />
                              <span className="truncate">{resume.location}</span>
                            </div>
                          )}
                        </div>
                        
                        {/* Show snippet from parsed_data if available */}
                        {resume.parsed_data?.summary && (
                          <div className="mt-4 p-3 bg-gray-50 rounded-lg border border-gray-200">
                            <p className="text-sm text-gray-700 line-clamp-2">
                              {resume.parsed_data.summary.substring(0, 200)}...
                            </p>
                          </div>
                        )}
                      </div>
                      
                      <div className="flex lg:flex-col gap-2 lg:ml-4">
                        <button
                          onClick={() => navigate(`/resume/${resume.id}`)}
                          className="flex items-center justify-center gap-2 px-4 py-2 text-sm text-blue-600 hover:text-blue-800 hover:bg-blue-50 rounded-lg transition-all duration-200 border border-blue-200 hover:border-blue-300 transform hover:scale-105"
                          title="View Details"
                        >
                          <FiEye size={18} />
                          <span className="hidden sm:inline">View</span>
                        </button>
                        <button
                          onClick={() => navigate(`/resume/${resume.id}/edit`)}
                          className="flex items-center justify-center gap-2 px-4 py-2 text-sm text-green-600 hover:text-green-800 hover:bg-green-50 rounded-lg transition-all duration-200 border border-green-200 hover:border-green-300 transform hover:scale-105"
                          title="Edit Resume"
                        >
                          <FiEdit size={18} />
                          <span className="hidden sm:inline">Edit</span>
                        </button>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Search Tips */}
        {!searched && (
          <div className="bg-blue-50/80 backdrop-blur-lg rounded-2xl p-6 border border-blue-200/50">
            <h3 className="text-sm font-bold text-blue-800 mb-3 flex items-center gap-2">
              <span className="text-lg">💡</span>
              Search Tips
            </h3>
            <ul className="text-sm text-blue-700 space-y-2">
              <li className="flex items-start gap-2">
                <span className="text-blue-500 mt-0.5">•</span>
                <span>Use keywords to search for specific technologies or job titles</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-blue-500 mt-0.5">•</span>
                <span>Filter by location to find candidates in specific cities or regions</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-blue-500 mt-0.5">•</span>
                <span>Add skills to narrow down results to candidates with specific expertise</span>
              </li>
              <li className="flex items-start gap-2">
                <span className="text-blue-500 mt-0.5">•</span>
                <span>You can combine all three filters for more precise results</span>
              </li>
            </ul>
          </div>
        )}
      </div>

      {/* Add custom animations */}
      <style jsx>{`
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
      `}</style>
    </div>
  );
}

export default SearchPage;