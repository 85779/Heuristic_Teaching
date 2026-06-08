import { createBrowserRouter } from 'react-router-dom';
import Layout from '../components/layout/AppLayout';
import Dashboard from '../pages/Dashboard';
import Study from '../pages/Study';
import Profile from '../pages/Profile';
import Teaching from '../pages/Teaching';

export const router = createBrowserRouter([
  { element: <Layout />, children: [
    { path: '/', element: <Dashboard /> },
    { path: '/study', element: <Study /> },
    { path: '/profile/:id', element: <Profile /> },
    { path: '/teaching/:id', element: <Teaching /> },
  ]},
]);
