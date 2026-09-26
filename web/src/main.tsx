import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { App } from "./App";
import { FrameReview } from "./FrameReview";

createRoot(document.getElementById("root")!).render(
  <StrictMode>
    {window.location.pathname === '/frame-review' ? <FrameReview /> : <App />}
  </StrictMode>,
);
