import { useState } from 'react';
import { Link } from 'react-router-dom';

function LoginForm() {
    const [activeTab, setActiveTab] = useState('policyholder');
    const [showPassword, setShowPassword] = useState(false);
    const [isInvalidUser, setIsInvalidUser] = useState(false);
    const [isInvalidAgent, setIsInvalidAgent] = useState(false);

    const ToggleActiveTab = (tab: string) => {
        setActiveTab(tab);
        // Clear input values
        const username = document.getElementById('username') as HTMLInputElement;
        const agentCode = document.getElementById('agent-code') as HTMLInputElement;
        if (username) username.value = '';
        if (agentCode) agentCode.value = '';
        setIsInvalidAgent(false);
        setIsInvalidUser(false);
    }
    const togglePasswordVisibility = () => {
        setShowPassword(!showPassword);
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
            <form className={`user-login w-100 d-flex jsutify-content-center flex-column ${activeTab === "policyholder" ? "" : "d-none"}`}>
                <div className="form-group w-100 mb-2">
                    <label className="form-label small">
                        Policy Number
                    </label>
                    <input
                        type="text"
                        autoComplete='off'
                        className={`form-control ${isInvalidUser ? 'is-invalid' : ''}`}
                        id='username'
                        onBlur={(e) => setIsInvalidUser(e.target.value.trim() === '')}
                        onChange={(e) => {
                            if (e.target.value.trim() !== '') {
                                setIsInvalidUser(false);
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

                <div className="divider d-flex w-100 justify-items-center align-items-center w-75"> <span className='px-2'> OR </span></div>

                <div className="form-links mb-2 text-center">
                    <p className="register-link m-0">
                        New Agent: <Link to="/register">Register</Link>
                    </p>
                </div>
            </form>

            {/* ******************Agent HOLDER LOGIN *************************/}
            <form className={`agent-login w-100 d-flex jsutify-content-center flex-column ${activeTab === "agent" ? "" : "d-none"}`}>
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

                <div className="divider d-flex w-100 justify-items-center align-items-center w-75"> <span className='px-2'> OR </span></div>

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