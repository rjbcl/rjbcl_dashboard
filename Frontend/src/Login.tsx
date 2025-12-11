import 'bootstrap/dist/css/bootstrap.min.css';
import 'bootstrap-icons/font/bootstrap-icons.css';
import './Login.css'

interface LoginProps {
  children: React.ReactNode;
}

function Login({children}: LoginProps) {
  return (
    <div className="main vw-100">
      <div className="container vh-100 p-3 d-flex align-items-center justify-content-center">
        <div className="login-wrapper container p-0 row rounded-4 shadow-lg">

          {/* HERO SECTION */}
          <div className="hero-section rounded-start-4 col-md-7 col-sm-12 d-flex align-items-center">
            <div className="hero-content container text-white mx-5 px-5">
              <h3 className="hero-title fw-bolder mb-3">Welcome to<br /> Rastriya Jeewan Beema</h3>
              <p className="hero-description small">
                Rastriya Jeewan Beema Company Limited is the first life insurance
                company in Nepal which was established as its previous Name
                Rastriya Beema Sansthan. Established by the Government of Nepal.
              </p>
              <a target='blank' href="https://rbs.gov.np/"><button className='rounded-3 btn btn-outline-light'>Explore</button></a>
            </div>
            <div className="hero-overlay"></div>
          </div>


          {/* LOGIN SECTION */}
          <div className="login-section px-5 rounded-end-4 bg-light col-md-5 col-sm-12 container justify-content-center d-flex align-items-center p-4">
            <div className="login-card pxm-1 d-flex d-flex align-items-center flex-column">
              <div className="login-header justify-content-center d-flex mb-4">
                <img src="/images/rjbclogo.png" alt="RJBCL Logo" className='company-logo w-75' />
              </div>

              {/* ******FORMS HERE******* */}
              {children}

              <div className="login-footer w-75 text-center w-100 small text-muted pt-3 border-top">
                <p className='m-0'>© 2025 RJBCL. All rights reserved.</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

  );
}

export default Login;