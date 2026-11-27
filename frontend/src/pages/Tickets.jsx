
import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";

import {
  Alert,
  Box,
  Button,
  Chip,
  CircularProgress,
  Container,
  FormControl,
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
  TextField,
  Typography,
} from "@mui/material";

import AddIcon from "@mui/icons-material/Add";
import VisibilityIcon from "@mui/icons-material/Visibility";

import Navbar from "../components/layout/Navbar";
import api from "../api/axios";

function Tickets() {
  const navigate = useNavigate();

  const [tickets, setTickets] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [search, setSearch] = useState("");
  const [status, setStatus] = useState("");
  const [priority, setPriority] = useState("");

  useEffect(() => {
    const fetchTickets = async () => {
      setLoading(true);
      setError("");

      try {
        const params = {};

        if (search.trim()) {
          params.search = search.trim();
        }

        if (status) {
          params.status = status;
        }

        if (priority) {
          params.priority = priority;
        }

        const response = await api.get("/tickets", { params });

        setTickets(response.data);
      } catch (err) {
        setError(
          err.response?.data?.detail ||
          "Unable to retrieve tickets."
        );
      } finally {
        setLoading(false);
      }
    };

    const timeout = setTimeout(fetchTickets, 300);

    return () => clearTimeout(timeout);
  }, [search, status, priority]);

  const getStatusColor = (value) => {
    const colors = {
      open: "info",
      in_progress: "warning",
      waiting_on_employee: "secondary",
      resolved: "success",
      closed: "default",
    };

    return colors[value] || "default";
  };

  const getPriorityColor = (value) => {
    const colors = {
      low: "success",
      normal: "info",
      high: "warning",
      urgent: "error",
    };

    return colors[value] || "default";
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
        <Box
          display="flex"
          justifyContent="space-between"
          alignItems="center"
          flexWrap="wrap"
          gap={2}
          mb={4}
        >
          <Box>
            <Typography variant="h4" fontWeight="bold">
              My Tickets
            </Typography>

            <Typography color="text.secondary" mt={1}>
              View and track your support requests.
            </Typography>
          </Box>

          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => navigate("/tickets/new")}
          >
            Create Ticket
          </Button>
        </Box>

        <Paper elevation={2} sx={{ p: 3, mb: 3 }}>
          <Typography variant="h6" fontWeight="bold" mb={2}>
            Filter Tickets
          </Typography>

          <Box
            display="flex"
            gap={2}
            flexWrap="wrap"
          >
            <TextField
              label="Search by subject"
              value={search}
              onChange={(event) => setSearch(event.target.value)}
              sx={{ flex: 2, minWidth: 200 }}
            />

            <FormControl sx={{ flex: 1, minWidth: 160 }}>
              <InputLabel>Status</InputLabel>

              <Select
                value={status}
                label="Status"
                onChange={(event) => setStatus(event.target.value)}
              >
                <MenuItem value="">All Statuses</MenuItem>
                <MenuItem value="open">Open</MenuItem>
                <MenuItem value="in_progress">In Progress</MenuItem>
                <MenuItem value="waiting_on_employee">
                  Waiting on Employee
                </MenuItem>
                <MenuItem value="resolved">Resolved</MenuItem>
                <MenuItem value="closed">Closed</MenuItem>
              </Select>
            </FormControl>

            <FormControl sx={{ flex: 1, minWidth: 160 }}>
              <InputLabel>Priority</InputLabel>

              <Select
                value={priority}
                label="Priority"
                onChange={(event) => setPriority(event.target.value)}
              >
                <MenuItem value="">All Priorities</MenuItem>
                <MenuItem value="low">Low</MenuItem>
                <MenuItem value="normal">Normal</MenuItem>
                <MenuItem value="high">High</MenuItem>
                <MenuItem value="urgent">Urgent</MenuItem>
              </Select>
            </FormControl>
          </Box>
        </Paper>

        {error && (
          <Alert severity="error" sx={{ mb: 3 }}>
            {error}
          </Alert>
        )}

        {loading ? (
          <Box display="flex" justifyContent="center" py={6}>
            <CircularProgress />
          </Box>
        ) : tickets.length === 0 ? (
          <Alert severity="info">
            No tickets found. Try changing your filters or create a new ticket.
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
                  <TableCell align="center"><strong>Action</strong></TableCell>
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

                    <TableCell>
                      {new Date(ticket.created_at).toLocaleDateString()}
                    </TableCell>

                    <TableCell align="center">
                      <Button
                        size="small"
                        startIcon={<VisibilityIcon />}
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
      </Container>
    </>
  );
}

export default Tickets;
