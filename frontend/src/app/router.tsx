// Router configuration
import { createBrowserRouter } from "react-router-dom";
import { HomePage } from "../pages/HomePage";
import { DemoPage } from "../pages/DemoPage";
import { StudentPage } from "../pages/StudentPage";
import { ClassPage } from "../pages/ClassPage";
import { KnowledgePage } from "../pages/KnowledgePage";
import { AppLayout } from "../components/layout/AppLayout";

const router = createBrowserRouter([
  {
    path: "/",
    element: <AppLayout />,
    children: [
      { index: true, element: <HomePage /> },
      { path: "demo", element: <DemoPage /> },
      { path: "student/:id", element: <StudentPage /> },
      { path: "class", element: <ClassPage /> },
      { path: "knowledge", element: <KnowledgePage /> },
    ],
  },
]);

export { router };
