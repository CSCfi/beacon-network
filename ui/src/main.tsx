import React from "react";
import ReactDOM from "react-dom/client";
import "./index.css";
import RouterSwitch from "./RouterSwitch";
import { BrowserRouter } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "react-query";

const queryClient = new QueryClient();

ReactDOM.createRoot(document.getElementById("root") as HTMLElement).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <RouterSwitch />
      </BrowserRouter>
    </QueryClientProvider>
  </React.StrictMode>
);
