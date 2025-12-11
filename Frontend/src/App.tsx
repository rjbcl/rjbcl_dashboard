// In your router file (App.tsx or Routes.tsx)
import { Navigate, Routes, Route } from 'react-router-dom';
import Login from './Login';
import LoginForm from './Forms/LoginForm';
import RegisterForm from './Forms/RegisterForm';
import ForgotPasswordForm from './Forms/ForgotPwForm';

function App() {
  return (
    <Routes>
      {/* Default route - redirect to login */}
      <Route path="/" element={<Navigate to="/login" replace />} />
      
      {/* Login Route */}
      <Route path="/login" element={
        <Login>
          <LoginForm />
        </Login>
      } />

      {/* Register Route */}
      <Route path="/register" element={
        <Login>
          <RegisterForm />
        </Login>
      } />

      {/* Forgot Password Route */}
      <Route path="/forgot-password" element={
        <Login>
          <ForgotPasswordForm />
        </Login>
      } />

      {/* 404 - Catch all unknown routes */}
      <Route path="*" element={<Navigate to="/login" replace />} />
    </Routes>
  );
}

export default App;