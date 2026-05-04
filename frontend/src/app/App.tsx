import { BrowserRouter, Route, Routes } from "react-router-dom";
import { DashboardPage } from "../pages/dashboard/DashboardPage";
import { EntitiesPage } from "../pages/entities/EntitiesPage";

export function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<DashboardPage />} />
        <Route path="/entities" element={<EntitiesPage />} />
      </Routes>
    </BrowserRouter>
  );
}
