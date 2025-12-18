import { BrowserRouter, Routes, Route } from "react-router-dom";
import { ThemeProvider } from "./hooks/useTheme";
import { ToastProvider } from "./hooks/useToast";
import Navigation from "./components/layout/Navigation";
import Footer from "./components/layout/Footer";
import ToastContainer from "./components/common/Toast";
import HomePage from "./pages/HomePage";
import DownloadPage from "./pages/DownloadPage";
import HistoryPage from "./pages/HistoryPage";
import SettingsPage from "./pages/SettingsPage";
import ApiDocsPage from "./pages/ApiDocsPage";

function App() {
  return (
    <ThemeProvider>
      <ToastProvider>
        <BrowserRouter>
          <div className="app">
            <a href="#main-content" className="skip-link">
              Skip to main content
            </a>
            <Navigation />
            <main id="main-content" className="main-content">
              <Routes>
                <Route path="/" element={<HomePage />} />
                <Route path="/download" element={<DownloadPage />} />
                <Route path="/history" element={<HistoryPage />} />
                <Route path="/settings" element={<SettingsPage />} />
                <Route path="/api-docs" element={<ApiDocsPage />} />
              </Routes>
            </main>
            <Footer />
            <ToastContainer />
          </div>
        </BrowserRouter>
      </ToastProvider>
    </ThemeProvider>
  );
}

export default App;
