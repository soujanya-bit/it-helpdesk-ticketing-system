
import { useCallback, useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";

import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  CircularProgress,
  Container,
  Divider,
  FormControl,
  InputLabel,
  MenuItem,
  Select,
  Typography,
} from "@mui/material";

import Navbar from "../components/layout/Navbar";
import Comments from "../components/tickets/Comments";
import TicketHistory from "../components/tickets/TicketHistory";
import { useAuth } from "../context/AuthContext";
import api from "../api/axios";

function TicketDetails() {
  const { ticketId } = useParams();
  const navigate = useNavigate();
  const { user } = useAuth();

  const [ticket, setTicket] = useState(null);
  const [loading, setLoading] = useState(true);
  const [updatingStatus, setUpdatingStatus] = useState(false);
  const [updatingPriority, setUpdatingPriority] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  const canManageTicket = ["agent", "admin"].includes(user?.role);

  const fetchTicket = useCallback(async () => {
    try {
      setError("");

      const response = await api.get(`/tickets/${ticketId}`);
      setTicket(response.data);
    } catch (err) {
      setError(
        err.response?.data?.detail ||
          "Unable to load ticket details."
      );
    } finally {
      setLoading(false);
    }
  }, [ticketId]);

  useEffect(() => {
    fetchTicket();
  }, [fetchTicket]);

  const formatDate = (date) => {
    if (!date) return "Not available";

    return new Date(date).toLocaleString();
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

  const statusTransitions = {
    open: ["in_progress"],
    in_progress: ["waiting_on_employee", "resolved"],
    waiting_on_employee: ["in_progress", "resolved"],
    resolved: ["closed", "in_progress"],
    closed: [],
  };

  const availableStatuses =
    statusTransitions[ticket?.status] || [];

  const handleStatusChange = async (event) => {
    const newStatus = event.target.value;

    try {
      setUpdatingStatus(true);
      setError("");
      setSuccess("");

      await api.patch(`/tickets/${ticketId}/status`, {
        status: newStatus,
      });

      await fetchTicket();

      setSuccess(
        `Ticket status updated to ${formatLabel(newStatus)}.`
      );
    } catch (err) {
      setError(
        err.response?.data?.detail ||
          "Unable to update ticket status."
      );
    } finally {
      setUpdatingStatus(false);
    }
  };

  const handlePriorityChange = async (event) => {
    const newPriority = event.target.value;

    try {
      setUpdatingPriority(true);
      setError("");
      setSuccess("");

      await api.patch(`/tickets/${ticketId}/priority`, {
        priority: newPriority,
      });

      await fetchTicket();

      setSuccess(
        `Ticket priority updated to ${formatLabel(newPriority)}.`
      );
    } catch (err) {
      setError(
        err.response?.data?.detail ||
          "Unable to update ticket priority."
      );
    } finally {
      setUpdatingPriority(false);
    }
  };

  const handleBack = () => {
    if (user?.role === "agent") {
      navigate("/agent");
    } else {
      navigate("/dashboard");
    }
  };

  return (
    <>
      <Navbar />

      <Container maxWidth="md" sx={{ py: 5 }}>
        <Button
          variant="outlined"
          onClick={handleBack}
          sx={{ mb: 3 }}
        >
          Back to Dashboard
        </Button>

        {loading && (
          <Box display="flex" justifyContent="center" py={6}>
            <CircularProgress />
          </Box>
        )}

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

        {ticket && !loading && (
          <>
            <Typography
              variant="h4"
              fontWeight="bold"
              gutterBottom
            >
              Ticket Details
            </Typography>

            <Typography
              variant="body2"
              color="text.secondary"
              mb={3}
            >
              Ticket ID: {ticket.id}
            </Typography>

            <Card elevation={2}>
              <CardContent sx={{ p: 4 }}>
                <Typography
                  variant="h5"
                  fontWeight="bold"
                  gutterBottom
                >
                  {ticket.subject}
                </Typography>

                <Box
                  display="flex"
                  gap={1}
                  flexWrap="wrap"
                  mb={3}
                >
                  <Chip
                    label={formatLabel(ticket.status)}
                    color={getStatusColor(ticket.status)}
                  />

                  <Chip
                    label={`Priority: ${formatLabel(ticket.priority)}`}
                    color={getPriorityColor(ticket.priority)}
                  />
                </Box>

                {canManageTicket && (
                  <>
                    <Divider sx={{ mb: 3 }} />

                    <Typography
                      variant="h6"
                      fontWeight="bold"
                      gutterBottom
                    >
                      Manage Ticket
                    </Typography>

                    <Box
                      display="flex"
                      flexDirection={{ xs: "column", sm: "row" }}
                      gap={2}
                      mb={3}
                    >
                      <FormControl fullWidth>
                        <InputLabel id="status-label">
                          Update Status
                        </InputLabel>

                        <Select
                          labelId="status-label"
                          value={ticket.status}
                          label="Update Status"
                          onChange={handleStatusChange}
                          disabled={
                            updatingStatus ||
                            availableStatuses.length === 0
                          }
                        >
                          {[
                            ticket.status,
                            ...availableStatuses,
                          ].map((status) => (
                            <MenuItem
                              key={status}
                              value={status}
                            >
                              {formatLabel(status)}
                            </MenuItem>
                          ))}
                        </Select>
                      </FormControl>

                      <FormControl fullWidth>
                        <InputLabel id="priority-label">
                          Update Priority
                        </InputLabel>

                        <Select
                          labelId="priority-label"
                          value={ticket.priority}
                          label="Update Priority"
                          onChange={handlePriorityChange}
                          disabled={updatingPriority}
                        >
                          {[
                            "low",
                            "normal",
                            "high",
                            "urgent",
                          ].map((priority) => (
                            <MenuItem
                              key={priority}
                              value={priority}
                            >
                              {formatLabel(priority)}
                            </MenuItem>
                          ))}
                        </Select>
                      </FormControl>
                    </Box>

                    {(updatingStatus || updatingPriority) && (
                      <Box display="flex" alignItems="center" gap={1} mb={2}>
                        <CircularProgress size={18} />
                        <Typography variant="body2" color="text.secondary">
                          Updating ticket...
                        </Typography>
                      </Box>
                    )}
                  </>
                )}

                <Divider sx={{ mb: 3 }} />

                <Typography
                  variant="subtitle1"
                  fontWeight="bold"
                  gutterBottom
                >
                  Description
                </Typography>

                <Typography
                  variant="body1"
                  sx={{
                    whiteSpace: "pre-wrap",
                    mb: 3,
                  }}
                >
                  {ticket.description}
                </Typography>

                <Divider sx={{ mb: 3 }} />

                <Typography
                  variant="subtitle1"
                  fontWeight="bold"
                  gutterBottom
                >
                  Ticket Information
                </Typography>

                <Box display="flex" flexDirection="column" gap={2}>
                  <Box>
                    <Typography variant="body2" color="text.secondary">
                      Category
                    </Typography>
                    <Typography>{ticket.category}</Typography>
                  </Box>

                  <Box>
                    <Typography variant="body2" color="text.secondary">
                      Requester ID
                    </Typography>
                    <Typography>{ticket.requester_id}</Typography>
                  </Box>

                  <Box>
                    <Typography variant="body2" color="text.secondary">
                      Assigned Agent ID
                    </Typography>
                    <Typography>
                      {ticket.assignee_id || "Not assigned"}
                    </Typography>
                  </Box>

                  <Box>
                    <Typography variant="body2" color="text.secondary">
                      Created At
                    </Typography>
                    <Typography>
                      {formatDate(ticket.created_at)}
                    </Typography>
                  </Box>

                  <Box>
                    <Typography variant="body2" color="text.secondary">
                      Last Updated
                    </Typography>
                    <Typography>
                      {formatDate(ticket.updated_at)}
                    </Typography>
                  </Box>

                  {ticket.resolved_at && (
                    <Box>
                      <Typography variant="body2" color="text.secondary">
                        Resolved At
                      </Typography>
                      <Typography>
                        {formatDate(ticket.resolved_at)}
                      </Typography>
                    </Box>
                  )}

                  {ticket.closed_at && (
                    <Box>
                      <Typography variant="body2" color="text.secondary">
                        Closed At
                      </Typography>
                      <Typography>
                        {formatDate(ticket.closed_at)}
                      </Typography>
                    </Box>
                  )}
                </Box>
              </CardContent>
            </Card>

            <Comments ticketId={ticket.id} />

            <TicketHistory ticketId={ticket.id} />
          </>
        )}
      </Container>
    </>
  );
}

export default TicketDetails;
