
import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import {
  Alert,
  Box,
  Card,
  CardContent,
  Chip,
  CircularProgress,
  Container,
  Grid,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
  Button,
} from "@mui/material";

import Navbar from "../components/layout/Navbar";
import api from "../api/axios";

function AgentDashboard() {
  const navigate = useNavigate();

  const [tickets, setTickets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const fetchTickets = async () => {
      try {
        const response = await api.get("/tickets");
        setTickets(response.data);
      } catch (err) {
        setError(
          err.response?.data?.detail ||
            "Unable to load assigned tickets."
        );
      } finally {
        setLoading(false);
      }
    };

    fetchTickets();
  }, []);

  const countStatus = (status) => {
    return tickets.filter(
      (ticket) => ticket.status === status
    ).length;
  };

  const getPriorityColor = (priority) => {
    const colors = {
      low: "success",
      normal: "info",
      high: "warning",
      urgent: "error",
    };

    return colors[priority] || "default";
  };

  const getStatusColor = (status) => {
    const colors = {
      open: "info",
      in_progress: "warning",
      waiting_on_employee: "secondary",
      resolved: "success",
      closed: "default",
    };

    return colors[status] || "default";
  };

  const formatLabel = (value) => {
    if (!value) return "";

    return value
      .replaceAll("_", " ")
      .replace(/\b\w/g, (char) => char.toUpperCase());
  };

  return (
    <>
      <Navbar />

      <Container maxWidth="xl" sx={{ py: 5 }}>
        <Typography variant="h4" fontWeight="bold" gutterBottom>
          Agent Dashboard
        </Typography>

        <Typography color="text.secondary" mb={4}>
          Monitor and manage your assigned support tickets.
        </Typography>

        {error && (
          <Alert severity="error" sx={{ mb: 3 }}>
            {error}
          </Alert>
        )}

        {loading ? (
          <Box display="flex" justifyContent="center" py={6}>
            <CircularProgress />
          </Box>
        ) : (
          <>
            <Grid container spacing={3}>
              {[
                {
                  label: "Assigned Tickets",
                  value: tickets.length,
                },
                {
                  label: "Open",
                  value: countStatus("open"),
                },
                {
                  label: "In Progress",
                  value: countStatus("in_progress"),
                },
                {
                  label: "Resolved",
                  value: countStatus("resolved"),
                },
              ].map((stat) => (
                <Grid
                  key={stat.label}
                  size={{ xs: 12, sm: 6, md: 3 }}
                >
                  <Card elevation={2}>
                    <CardContent>
                      <Typography
                        color="text.secondary"
                        variant="body2"
                      >
                        {stat.label}
                      </Typography>

                      <Typography
                        variant="h4"
                        fontWeight="bold"
                        sx={{ mt: 1 }}
                      >
                        {stat.value}
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
              ))}
            </Grid>

            <Box mt={5} mb={2}>
              <Typography variant="h5" fontWeight="bold">
                Assigned Tickets
              </Typography>
            </Box>

            {tickets.length === 0 ? (
              <Alert severity="info">
                You currently have no assigned tickets.
              </Alert>
            ) : (
              <TableContainer component={Paper} elevation={2}>
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell><strong>Subject</strong></TableCell>
                      <TableCell><strong>Category</strong></TableCell>
                      <TableCell><strong>Status</strong></TableCell>
                      <TableCell><strong>Priority</strong></TableCell>
                      <TableCell><strong>Created</strong></TableCell>
                      <TableCell align="center">
                        <strong>Action</strong>
                      </TableCell>
                    </TableRow>
                  </TableHead>

                  <TableBody>
                    {tickets.map((ticket) => (
                      <TableRow key={ticket.id} hover>
                        <TableCell>
                          <Typography fontWeight="medium">
                            {ticket.subject}
                          </Typography>
                        </TableCell>

                        <TableCell>{ticket.category}</TableCell>

                        <TableCell>
                          <Chip
                            size="small"
                            label={formatLabel(ticket.status)}
                            color={getStatusColor(ticket.status)}
                          />
                        </TableCell>

                        <TableCell>
                          <Chip
                            size="small"
                            label={formatLabel(ticket.priority)}
                            color={getPriorityColor(ticket.priority)}
                          />
                        </TableCell>

                        <TableCell>
                          {new Date(
                            ticket.created_at
                          ).toLocaleDateString()}
                        </TableCell>

                        <TableCell align="center">
                          <Button
                            size="small"
                            onClick={() =>
                              navigate(`/tickets/${ticket.id}`)
                            }
                          >
                            View Ticket
                          </Button>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            )}
          </>
        )}
      </Container>
    </>
  );
}

export default AgentDashboard;
