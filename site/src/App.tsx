import { Routes, Route } from "react-router-dom";
import Layout from "./components/Layout";
import Home from "./pages/Home";
import HowItWorks from "./pages/HowItWorks";
import CLI from "./pages/CLI";
import API from "./pages/API";

export default function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/how-it-works" element={<HowItWorks />} />
        <Route path="/cli" element={<CLI />} />
        <Route path="/api" element={<API />} />
      </Routes>
    </Layout>
  );
}
