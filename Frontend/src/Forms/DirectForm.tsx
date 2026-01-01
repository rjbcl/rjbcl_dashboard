import { useState, useEffect } from "react";
import { NepaliDatePicker } from "nepali-datepicker-reactjs";
import "nepali-datepicker-reactjs/dist/index.css";

function DirectForm() {
    const [dobBS, setDobBS] = useState("");
    const [dobAD, setDobAD] = useState("");
    const [policyNumber, setPolicyNumber] = useState("");
    const [errorMessage, setErrorMessage] = useState("");
    const [isLoading, setIsLoading] = useState(false);
    const [_csrfToken, setCsrfToken] = useState("");

    const API_BASE_URL = 'http://localhost:8000/api/auth';

    // Get CSRF token on component mount
    useEffect(() => {
        const fetchCSRFToken = async () => {
            try {
                const response = await fetch(`${API_BASE_URL}/csrf/`, {
                    method: 'GET',
                    credentials: 'include',
                    headers: {
                        'Accept': 'application/json',
                        'Content-Type': 'application/json',
                    },
                });
                
                if (response.ok) {
                    const data = await response.json();
                    console.log('CSRF response:', data);
                    
                    const tokenFromCookie = getCookie('csrftoken');
                    console.log('CSRF token from cookie:', tokenFromCookie);
                    
                    if (tokenFromCookie) {
                        setCsrfToken(tokenFromCookie);
                    } else if (data.csrfToken) {
                        setCsrfToken(data.csrfToken);
                    }
                }
            } catch (err) {
                console.error('Error fetching CSRF token:', err);
            }
        };
        
        fetchCSRFToken();
    }, []);

    // Helper function to get cookie
    const getCookie = (name: string): string => {
        let cookieValue = '';
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setErrorMessage('');

        // Validation
        if (!policyNumber.trim()) {
            setErrorMessage('Policy number is required');
            return;
        }

        if (!dobAD.trim()) {
            setErrorMessage('Date of birth is required');
            return;
        }

        // Get fresh CSRF token
        const currentCsrfToken = getCookie('csrftoken');
        console.log('Using CSRF token:', currentCsrfToken);

        if (!currentCsrfToken) {
            setErrorMessage('Security token missing. Please refresh the page.');
            return;
        }

        setIsLoading(true);

        try {
            const response = await fetch(`${API_BASE_URL}/direct-kyc/`, {
                method: 'POST',
                headers: {
                    'Accept': 'application/json',
                    'Content-Type': 'application/json',
                    'X-CSRFToken': currentCsrfToken,
                },
                credentials: 'include',
                body: JSON.stringify({
                    policy_no: policyNumber,
                    dob_ad: dobAD,
                }),
            });

            const data = await response.json();
            console.log('Full response data:', data);

            if (response.ok) {
                console.log('Direct KYC access granted:', data);
                console.log('Redirect URL:', data.redirect_url);
                
                if (data.redirect_url) {
                    console.log('Redirecting to:', data.redirect_url);
                    window.location.href = data.redirect_url;
                }
            } else {
                console.log('Access denied:', data);
                setErrorMessage(data.error || 'Access denied. Please check your details.');
            }
        } catch (error) {
            console.error('Direct KYC error:', error);
            setErrorMessage('Network error. Please check your connection and try again.');
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <>
            <div className="form-container direct-form w-100" id="directkyc">
                <form onSubmit={handleSubmit} autoComplete="off">
                    <div className="form-group mb-2">
                        <label className="form-label small fw-semibold">Policy Number</label>
                        <input 
                            className="form-control" 
                            name="Policy_no" 
                            id="phone-number"
                            placeholder="POL123" 
                            autoComplete="off" 
                            required
                            value={policyNumber}
                            onChange={(e) => {
                                setPolicyNumber(e.target.value);
                                setErrorMessage('');
                            }}
                            disabled={isLoading}
                        />
                    </div>

                    <div className="row mb-2">
                        <div className="form-group mb-2 col">
                            <label className="form-label small fw-semibold">DOB (BS)</label>
                            <NepaliDatePicker
                                inputClassName="form-control"
                                value={dobBS}
                                onChange={(value) => {
                                    setDobBS(value);
                                    setErrorMessage('');
                                }}
                                options={{ calenderLocale: "ne", valueLocale: "en" }}
                                disabled={isLoading}
                            />
                        </div>
                        <div className="form-group mb-2 col">
                            <label className="form-label small fw-semibold">DOB (AD)</label>
                            <input
                                className="form-control"
                                name="user_dob_ad"
                                type="date"
                                required
                                value={dobAD}
                                onChange={(e) => {
                                    setDobAD(e.target.value);
                                    setErrorMessage('');
                                }}
                                onFocus={(e) => (e.target as HTMLInputElement).showPicker()}
                                onClick={(e) => (e.target as HTMLInputElement).showPicker()}
                                disabled={isLoading}
                            />
                        </div>
                    </div>

                    <div className="form-footer mb-2">
                        <div>
                            <span className="error-message text-danger">{errorMessage}</span>
                        </div>
                    </div>

                    <button
                        type='submit'
                        className="btn-signin w-100 bg-primary rounded-3 small mb-3 p-2"
                        disabled={isLoading}
                    >
                        {isLoading ? 'Verifying...' : 'Continue'}
                    </button>

                    <div className="divider d-flex w-100 justify-items-center align-items-center">
                        <span className='px-2'> OR </span>
                    </div>

                    <div className="form-links mb-2 text-center">
                        <p className="register-link m-0">
                            Already Have an Account? <a href="/">Login</a>
                        </p>
                    </div>
                </form>
            </div>
        </>
    );
}

export default DirectForm;