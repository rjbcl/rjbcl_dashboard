// import { useState } from 'react';


function RegisterForm() {

    return (
        <>
            <div className="form-container" id="agentFormWrapper">
                        <form id="agentForm" method="POST" action="{% url 'kyc:agent_register' %}" autoComplete="off">

                            <div className="row g-1 mb-1">
                                <h5 className="border-bottom pb-2 mb-3 fw-bold">    
                                    Agent Registration
                                </h5>
                            </div>
                            <div className="row g-2">
                                <div className="col-md-6">
                                    <div className="form-group">
                                        <label className="form-label">First Name</label>
                                        <input className="form-control" name="first_name" id="agent-first-name"
                                            placeholder="John" autoComplete="off" required />
                                    </div>
                                </div>
                                <div className="col-md-6">
                                    <div className="form-group">
                                        <label className="form-label">Last Name</label>
                                        <input className="form-control" name="last_name" id="agent-last-name"
                                            placeholder="Doe" autoComplete="off" required />
                                    </div>
                                </div>
                            </div>

                            <div className="form-group">
                                <label className="form-label">Phone Number</label>
                                <input className="form-control" name="phone_number" id="phone-number"
                                    placeholder="98XXXXXXXX" autoComplete="off" required />
                            </div>

                            <div className="form-group">
                                <label className="form-label">License Number</label>
                                <input className="form-control" name="License_no" type="text" id="License_no"
                                    placeholder="LIC-XXX" required />
                            </div>

                            <div className="form-group">
                                <label className="form-label">Agent Code</label>
                                <input className="form-control" name="agent_code" id="agent_code" placeholder="AGT123"
                                    autoComplete="off" required />
                            </div>

                            <div className="form-footer mb-2">
                                <div>
                                    <span className="error-message text-danger"></span>
                                </div>
                            </div>

                            <button type="submit" className="btn-signin">
                                Register
                            </button>

                            <div className="divider">
                                <span>OR</span>
                            </div>

                            <div className="form-links">
                                <p className="register-link">
                                    Already have an account? <a href="/auth/agent/?tab=agent">Login</a>
                                </p>
                            </div>
                        </form>
                    </div>
        </>
    );
}


export default RegisterForm;