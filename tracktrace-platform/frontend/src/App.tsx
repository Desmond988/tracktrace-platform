import { Route, Routes } from "react-router-dom";
import PublicLayout from "./components/PublicLayout";
import Home from "./pages/public/Home";
import Track from "./pages/public/Track";
import Login from "./pages/public/Login";
import Register from "./pages/public/Register";
import ForgotPassword from "./pages/public/ForgotPassword";
import ResetPassword from "./pages/public/ResetPassword";
import Quote from "./pages/public/Quote";
import Contact from "./pages/public/Contact";
import Services from "./pages/public/Services";
import ServiceDetail from "./pages/public/ServiceDetail";
import About from "./pages/public/About";
import PublicLocations from "./pages/public/Locations";
import Careers from "./pages/public/Careers";
import Legal from "./pages/public/Legal";
import Faq from "./pages/public/Faq";
import NotFound from "./pages/public/NotFound";
import CustomerDashboard from "./pages/customer/Dashboard";
import CustomerShipmentDetail from "./pages/customer/ShipmentDetail";
import CustomerNotifications from "./pages/customer/Notifications";
import CustomerProfile from "./pages/customer/Profile";
import StaffLayout from "./pages/admin/StaffLayout";
import AdminDashboard from "./pages/admin/Dashboard";
import AdminShipments from "./pages/admin/Shipments";
import ShipmentDetailPage from "./pages/admin/ShipmentDetail";
import ShipmentCreate from "./pages/admin/ShipmentCreate";
import Customers from "./pages/admin/Customers";
import Users from "./pages/admin/Users";
import Quotes from "./pages/admin/Quotes";
import Messages from "./pages/admin/Messages";
import AuditLogs from "./pages/admin/AuditLogs";
import NotificationsLog from "./pages/admin/NotificationsLog";
import Reports from "./pages/admin/Reports";
import Statuses from "./pages/admin/Statuses";
import Locations from "./pages/admin/Locations";
import LegalAdmin from "./pages/admin/Legal";
import FaqAdmin from "./pages/admin/Faq";
import Settings from "./pages/admin/Settings";
import { RequireCustomer, RequireStaff } from "./components/RouteGuards";

export default function App() {
  return (
    <Routes>
      <Route element={<PublicLayout />}>
        <Route index element={<Home />} />
        <Route path="track" element={<Track />} />
        <Route path="track/:trackingNumber" element={<Track />} />
        <Route path="services" element={<Services />} />
        <Route path="services/:slug" element={<ServiceDetail />} />
        <Route path="about" element={<About />} />
        <Route path="locations" element={<PublicLocations />} />
        <Route path="careers" element={<Careers />} />
        <Route path="quote" element={<Quote />} />
        <Route path="contact" element={<Contact />} />
        <Route path="faq" element={<Faq />} />
        <Route path="legal/:slug" element={<Legal />} />
        <Route path="login" element={<Login />} />
        <Route path="register" element={<Register />} />
        <Route path="forgot-password" element={<ForgotPassword />} />
        <Route path="reset-password" element={<ResetPassword />} />
        <Route path="account" element={<RequireCustomer><CustomerDashboard /></RequireCustomer>} />
        <Route path="account/shipments/:id" element={<RequireCustomer><CustomerShipmentDetail /></RequireCustomer>} />
        <Route path="account/notifications" element={<RequireCustomer><CustomerNotifications /></RequireCustomer>} />
        <Route path="account/profile" element={<RequireCustomer><CustomerProfile /></RequireCustomer>} />
      </Route>
      <Route path="staff" element={<RequireStaff><StaffLayout /></RequireStaff>}>
        <Route index element={<AdminDashboard />} />
        <Route path="shipments" element={<AdminShipments />} />
        <Route path="shipments/create" element={<ShipmentCreate />} />
        <Route path="shipments/:id" element={<ShipmentDetailPage />} />
        <Route path="customers" element={<Customers />} />
        <Route path="users" element={<Users />} />
        <Route path="quotes" element={<Quotes />} />
        <Route path="messages" element={<Messages />} />
        <Route path="audit-logs" element={<AuditLogs />} />
        <Route path="notifications" element={<NotificationsLog />} />
        <Route path="reports" element={<Reports />} />
        <Route path="statuses" element={<Statuses />} />
        <Route path="locations" element={<Locations />} />
        <Route path="legal" element={<LegalAdmin />} />
        <Route path="faq" element={<FaqAdmin />} />
        <Route path="settings" element={<Settings />} />
      </Route>
      <Route path="*" element={<NotFound />} />
    </Routes>
  );
}
