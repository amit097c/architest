import React from "react";
import { Routes, Route, Navigate } from "react-router-dom";
import { ArchiTestProvider } from "@/context/ArchiTestContext";
import Header from "@/components/navigation/Header";
import HomePage from "@/pages/HomePage";
import HistoryPage from "@/pages/HistoryPage";
import TestEditPage from "@/pages/TestEditPage";
import CollectionsPage from "@/pages/CollectionsPage";
import CollectionDetailsPage from "@/pages/CollectionDetailsPage";
import DashboardPage from "@/pages/DashboardPage";
import TestRunPage from "@/pages/TestRunPage";
import IntegrationsPage from "@/pages/IntegrationsPage";

const App: React.FC = () => {
  return (
    <ArchiTestProvider>
      <div className="min-h-screen flex flex-col bg-background">
        <Header />
        <main className="flex-1 container mx-auto p-4 sm:p-6 pt-6">
          <Routes>
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
            <Route path="/create" element={<HomePage />} />
            <Route path="/dashboard" element={<DashboardPage />} />
            <Route path="/history" element={<HistoryPage />} />
            <Route path="/edit/:id" element={<TestEditPage />} />
            <Route path="/collections" element={<CollectionsPage />} />
            <Route path="/collection/:id" element={<CollectionDetailsPage />} />
            <Route path="*" element={<Navigate to="/dashboard" replace />} />
          </Routes>
        </main>
      </div>
    </ArchiTestProvider>
  );
};

export default App;
