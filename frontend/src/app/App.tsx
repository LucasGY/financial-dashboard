import { BrowserRouter, Route, Routes } from "react-router-dom";
import { LanguageToggle } from "../components/ui/LanguageToggle";
import { ThemeToggle } from "../components/ui/ThemeToggle";
import { DashboardPage } from "../pages/dashboard/DashboardPage";
import { EntitiesPage } from "../pages/entities/EntitiesPage";
import { LanguageProvider } from "./language";
import { ThemeProvider } from "./theme";

export function App() {
  return (
    <ThemeProvider>
      <LanguageProvider>
        <BrowserRouter>
          <div className="fixed right-4 top-4 z-[60] flex flex-wrap justify-end gap-2">
            <LanguageToggle />
            <ThemeToggle />
          </div>
          <Routes>
            <Route path="/" element={<DashboardPage />} />
            <Route path="/entities" element={<EntitiesPage />} />
          </Routes>
        </BrowserRouter>
      </LanguageProvider>
    </ThemeProvider>
  );
}
