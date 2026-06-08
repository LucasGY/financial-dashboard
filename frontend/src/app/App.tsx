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
          <div className="sticky top-0 z-[60] flex flex-wrap justify-end gap-2 border-b border-slate-200 bg-white/95 px-3 py-2 backdrop-blur dark:border-slate-800 dark:bg-slate-950/95 sm:fixed sm:right-4 sm:top-4 sm:border-0 sm:bg-transparent sm:p-0 sm:dark:bg-transparent">
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
