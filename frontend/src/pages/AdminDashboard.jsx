
import { useCallback, useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  CircularProgress,
  Container,
  FormControl,
  Grid,
  InputLabel,
  MenuItem,
  Paper,
  Select,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
} from "@mui/material";

import Navbar from "../components/layout/Navbar";
import api from "../api/axios";

function AdminDashboard() {
  const navigate = useNavigate();

  const [tickets, setTickets] = useState([]);
  const [agents, setAgents] = useState([]);
  const [loading, setLoading] = useState(true);
  const [assigningTicket, setAssigningTicket] = useState(null);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const fetchDashboardData = useCallback(async () => {
    try {
      setError("");

      const [ticketResponse, agentResponse] = await Promise.all([
        api.get("/tickets/"),
        api.get("/auth/agents"),
      ]);

      setTickets(ticketResponse.data);
      setAgents(agentResponse.data);
    } catch (err) {
      setError(
        err.response?.data?.detail ||
          "Unable to load admin dashboard."
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchDashboardData();
  }, [fetchDashboardData]);

  const handleAssignment = async (ticketId, agentId) => {
    if (!agentId) return;

    try {
      setAssigningTicket(ticketId);
      setError("");
      setSuccess("");

      const response = await api.patch(
        `/tickets/${ticketId}/assign`,
        {
          assignee_id: agentId,
        }
      );

      setTickets((previousTickets) =>
        previousTickets.map((ticket) =>
          ticket.id === ticketId ? response.data : ticket
        )
      );

      setSuccess("Ticket assigned successfully.");
    } catch (err) {
      setError(
        err.response?.data?.detail ||
          "Unable to assign ticket."
      );
    } finally {
      setAssigningTicket(null);
    }
  };

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
          Admin Dashboard
        </Typography>

        <Typography color="text.secondary" mb={4}>
          Manage support tickets and assign them to agents.
        </Typography>

        {error && (
          <Alert severity="error" sx={{ mb: 3 }}>
            {error}
          </Alert>
        )}

        {success && (
          <Alert severity="success" sx={{ mb: 3 }}>
            {success}
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
                  label: "Total Tickets",
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
                {
                  label: "Unassigned",
                  value: tickets.filter(
                    (ticket) => !ticket.assignee_id
                  ).length,
                },
                {
                  label: "Available Agents",
                  value: agents.length,
                },
              ].map((stat) => (
                <Grid
                  key={stat.label}
                  size={{ xs: 12, sm: 6, md: 4, lg: 2 }}
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
                Ticket Management
              </Typography>

              <Typography color="text.secondary" variant="body2">
                Assign or reassign tickets to available agents.
              </Typography>
            </Box>

            {tickets.length === 0 ? (
              <Alert severity="info">
                No tickets have been created yet.
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
                      <TableCell><strong>Assignment</strong></TableCell>
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

                          <Typography
                            variant="caption"
                            color="text.secondary"
                          >
                            {ticket.id}
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

                        <TableCell sx={{ minWidth: 190 }}>
                          <FormControl fullWidth size="small">
                            <InputLabel id={`agent-${ticket.id}`}>
                              Assign Agent
                            </InputLabel>

                            <Select
                              labelId={`agent-${ticket.id}`}
                              value={ticket.assignee_id || ""}
                              label="Assign Agent"
                              disabled={
                                assigningTicket === ticket.id ||
                                agents.length === 0
                              }
                              onChange={(event) =>
                                handleAssignment(
                                  ticket.id,
                                  event.target.value
                                )
                              }
                            >
                              {agents.map((agent) => (
                                <MenuItem
                                  key={agent.id}
                                  value={agent.id}
                                >
                                  {agent.full_name}
                                </MenuItem>
                              ))}
                            </Select>
                          </FormControl>

                          {assigningTicket === ticket.id && (
                            <Typography
                              variant="caption"
                              color="text.secondary"
                            >
                              Assigning...
                            </Typography>
                          )}
                        </TableCell>

                        <TableCell align="center">
                          <Button
                            size="small"
                            onClick={() =>
                              navigate(`/tickets/${ticket.id}`)
                            }
                          >
                            View
                          </Button>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            )}

            {agents.length === 0 && (
              <Alert severity="warning" sx={{ mt: 3 }}>
                No active agents are available for assignment.
              </Alert>
            )}
          </>
        )}
      </Container>
    </>
  );
}

export default AdminDashboard;
