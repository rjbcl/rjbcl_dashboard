import { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';

function LoginForm() {
    const [activeTab, setActiveTab] = useState('policyholder');
    const [showPassword, setShowPassword] = useState(false);
    const [isInvalidUser, setIsInvalidUser] = useState(false);
    const [isInvalidAgent, setIsInvalidAgent] = useState(false);
    
    // Policy holder form states
    const [policyNumber, setPolicyNumber] = useState('');
    const [password, setPassword] = useState('');
    const [errorMessage, setErrorMessage] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [csrfToken, setCsrfToken] = useState('');
    
    const navigate = useNavigate();
    const API_BASE_URL = 'http://localhost:8000/api/auth';

    // Get CSRF token on component mount
    useEffect(() => {
        fetch(`${API_BASE_URL}/csrf/`, {
            credentials: 'include',
        })
        .then(res => res.json())
        .then(() => {
            const token = getCookie('csrftoken');
            setCsrfToken(token);
        })
        .catch(err => console.error('Error fetching CSRF token:', err));
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

    const ToggleActiveTab = (tab: string) => {
        setActiveTab(tab);
        // Clear input values
        setPolicyNumber('');
        setPassword('');
        setErrorMessage('');
        const username = document.getElementById('username') as HTMLInputElement;
        const agentCode = document.getElementById('agent-code') as HTMLInputElement;
        if (username) username.value = '';
        if (agentCode) agentCode.value = '';
        setIsInvalidAgent(false);
        setIsInvalidUser(false);
    };

    const togglePasswordVisibility = () => {
        setShowPassword(!showPassword);
    };

    // Handle policy holder login
    const handlePolicyHolderLogin = async (e: React.FormEvent) => {
        e.preventDefault();
        setErrorMessage('');

        // Validation
        if (policyNumber.trim() === '') {
            setIsInvalidUser(true);
            setErrorMessage('Policy number is required');
            return;
        }

        if (password.trim() === '') {
            setErrorMessage('Password is required');
            return;
        }

        setIsLoading(true);

        try {
            const response = await fetch(`${API_BASE_URL}/policyholder/login/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': csrfToken,
                },
                credentials: 'include',
                body: JSON.stringify({
                    policy_number: policyNumber,
                    password: password,
                }),
            });

            const data = await response.json();

            if (response.ok) {
                // Login successful
                console.log('Login successful:', data);
                // Redirect to dashboard or appropriate page
                navigate('/dashboard'); // Change this to your desired route
            } else {
                // Login failed
                setErrorMessage(data.error || 'Login failed. Please try again.');
                setIsInvalidUser(true);
            }
        } catch (error) {
            console.error('Login error:', error);
            setErrorMessage('Network error. Please check your connection and try again.');
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <>
            <div className="tab-buttons d-flex bg-dark-subtle rounded-2 justify-content-center w-100 mb-3 mx-2">
                <button
                    id="user_login"
                    className={`user-btn tab-btn small w-50 p-2 rounded-2 me-1 ${activeTab === 'policyholder' ? 'active' : ''}`}
                    onClick={() => ToggleActiveTab('policyholder')}
                >
                    Policy Holder
                </button>
                <button
                    className={`tab-btn small w-50 p-2 rounded-2 ms-1 ${activeTab === 'agent' ? 'active' : ''}`}
                    onClick={() => ToggleActiveTab('agent')}
                >
                    Agent
                </button>
            </div>

            {/* ****************** POLICY HOLDER LOGIN *************************/}
            <form 
                className={`user-login w-100 d-flex justify-content-center flex-column ${activeTab === "policyholder" ? "" : "d-none"}`}
                onSubmit={handlePolicyHolderLogin}
            >
                <div className="form-group w-100 mb-2">
                    <label className="form-label small">
                        Policy Number
                    </label>
                    <input
                        type="text"
                        autoComplete='off'
                        className={`form-control ${isInvalidUser ? 'is-invalid' : ''}`}
                        id='username'
                        value={policyNumber}
                        onBlur={(e) => {
                            if (e.target.value.trim() === '') {
                                setIsInvalidUser(true);
                                setErrorMessage('Policy number is required');
                            }
                        }}
                        onChange={(e) => {
                            setPolicyNumber(e.target.value);
                            if (e.target.value.trim() !== '') {
                                setIsInvalidUser(false);
                                setErrorMessage('');
                            }
                        }}
                        disabled={isLoading}
                    />
                </div>

                <div className="form-group w-100 mb-2">
                    <label className="form-label small">Password</label>
                    <input
                        type={showPassword ? "text" : "password"}
                        className="form-control"
                        value={password}
                        onChange={(e) => {
                            setPassword(e.target.value);
                            setErrorMessage('');
                        }}
                        disabled={isLoading}
                    />
                    <button
                        className='toggle-password'
                        type="button"
                        onClick={togglePasswordVisibility}
                        disabled={isLoading}
                    >
                        <i className={`bi ${showPassword ? 'bi-eye-slash' : 'bi-eye'}`}></i>
                    </button>
                </div>

                <div className="form-footer d-flex justify-content-between w-100 mb-2">
                    <div className="error-message small text-danger">
                        {errorMessage}
                    </div>
                    <div className="forgot-link">
                        <Link to="/forgot-password">Forgot Password?</Link>
                    </div>
                </div>

                <button 
                    type='submit' 
                    className="btn-signin w-100 bg-primary rounded-3 small mb-3 p-2"
                    disabled={isLoading}
                >
                    {isLoading ? 'Logging in...' : 'Login'}
                </button>

                <div className="divider d-flex w-100 justify-items-center align-items-center w-75">
                    <span className='px-2'> OR </span>
                </div>

                <div className="form-links mb-2 text-center">
                    <p className="register-link m-0">
                        <Link to="/direct">Continue Without Login</Link>
                    </p>
                </div>
            </form>

            {/* ******************AGENT LOGIN (NOT IMPLEMENTED YET) *************************/}
            <form className={`agent-login w-100 d-flex justify-content-center flex-column ${activeTab === "agent" ? "" : "d-none"}`}>
                <div className="form-group agent-login w-100 mb-2">
                    <label className="form-label small">
                        Agent Code
                    </label>
                    <input
                        type="text"
                        id='agent-code'
                        autoComplete='off'
                        className={`form-control ${isInvalidAgent ? 'is-invalid' : ''}`}
                        onBlur={(e) => setIsInvalidAgent(e.target.value.trim() === '')}
                        onChange={(e) => {
                            if (e.target.value.trim() !== '') {
                                setIsInvalidAgent(false);
                            }
                        }}
                    />
                </div>

                <div className="form-group w-100 mb-2">
                    <label className="form-label small">Password</label>
                    <input
                        type={showPassword ? "text" : "password"}
                        className="form-control"
                    />
                    <button
                        className='toggle-password'
                        type="button"
                        onClick={togglePasswordVisibility}
                    >
                        <i className={`bi ${showPassword ? 'bi-eye-slash' : 'bi-eye'}`}></i>
                    </button>
                </div>

                <div className="form-footer d-flex justify-content-between w-100 mb-2">
                    <div className="error-message small"></div>
                    <div className="forgot-link"><Link to="/forgot-password">Forgot Password?</Link></div>
                </div>

                <button type='submit' className="btn-signin w-100 bg-primary rounded-3 small mb-3 p-2">Login</button>

                <div className="divider d-flex w-100 justify-items-center align-items-center w-75">
                    <span className='px-2'> OR </span>
                </div>

                <div className="form-links mb-2 text-center">
                    <p className="register-link m-0">
                        New Agent: <Link to="/register">Register</Link>
                    </p>
                </div>
            </form>
        </>
    );
}

export default LoginForm;