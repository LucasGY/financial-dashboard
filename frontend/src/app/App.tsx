import { BrowserRouter, Route, Routes } from "react-router-dom";
import { ThemeToggle } from "../components/ui/ThemeToggle";
import { DashboardPage } from "../pages/dashboard/DashboardPage";
import { EntitiesPage } from "../pages/entities/EntitiesPage";
import { ThemeProvider } from "./theme";

export function App() {
  return (
    <ThemeProvider>
      <BrowserRouter>
        <ThemeToggle />
        <Routes>
          <Route path="/" element={<DashboardPage />} />
          <Route path="/entities" element={<EntitiesPage />} />
        </Routes>
      </BrowserRouter>
    </ThemeProvider>
  );
}
