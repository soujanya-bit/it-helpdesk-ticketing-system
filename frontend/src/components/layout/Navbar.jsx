
import {
  AppBar,
  Avatar,
  Box,
  Button,
  Toolbar,
  Typography,
} from "@mui/material";

import { useNavigate } from "react-router-dom";
import { useAuth } from "../../context/AuthContext";

function Navbar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();

  const dashboardPath = {
    employee: "/dashboard",
    agent: "/agent",
    admin: "/admin",
  };

  const currentDashboard = dashboardPath[user?.role] || "/dashboard";

  const handleLogout = () => {
    logout();
    navigate("/login", { replace: true });
  };

  const initials = user?.full_name
    ?.split(" ")
    .map((name) => name[0])
    .join("")
    .slice(0, 2)
    .toUpperCase();

  return (
    <AppBar position="static" elevation={1}>
      <Toolbar sx={{ gap: 2 }}>
        <Typography
          variant="h6"
          component="div"
          sx={{
            flexGrow: 1,
            fontWeight: "bold",
            cursor: "pointer",
          }}
          onClick={() => navigate(currentDashboard)}
        >
          IT Helpdesk
        </Typography>

        <Button
          color="inherit"
          onClick={() => navigate(currentDashboard)}
        >
          {user?.role === "agent"
            ? "Agent Dashboard"
            : user?.role === "admin"
              ? "Admin Dashboard"
              : "Dashboard"}
        </Button>

        {user?.role === "employee" && (
          <Button
            color="inherit"
            onClick={() => navigate("/tickets")}
          >
            My Tickets
          </Button>
        )}

        {user?.role === "agent" && (
          <Button
            color="inherit"
            onClick={() => navigate("/agent")}
          >
            Assigned Tickets
          </Button>
        )}

        {user?.role === "admin" && (
          <Button
            color="inherit"
            onClick={() => navigate("/admin")}
          >
            Ticket Management
          </Button>
        )}

        <Box
          sx={{
            display: "flex",
            alignItems: "center",
            gap: 2,
          }}
        >
          <Box sx={{ textAlign: "right" }}>
            <Typography variant="body2" fontWeight="bold">
              {user?.full_name}
            </Typography>

            <Typography
              variant="caption"
              sx={{
                opacity: 0.8,
                textTransform: "capitalize",
              }}
            >
              {user?.role}
            </Typography>
          </Box>

          <Avatar sx={{ bgcolor: "secondary.main" }}>
            {initials}
          </Avatar>

          <Button
            color="inherit"
            variant="outlined"
            onClick={handleLogout}
          >
            Logout
          </Button>
        </Box>
      </Toolbar>
    </AppBar>
  );
}

export default Navbar;
