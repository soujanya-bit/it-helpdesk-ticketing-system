
import { useEffect, useState } from "react";

import {
  Alert,
  Box,
  CircularProgress,
  Divider,
  Paper,
  Typography,
} from "@mui/material";

import HistoryIcon from "@mui/icons-material/History";
import api from "../../api/axios";

function TicketHistory({ ticketId }) {
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const fetchHistory = async () => {
      setLoading(true);
      setError("");

      try {
        const response = await api.get(
          `/tickets/${ticketId}/history`
        );

        setHistory(response.data);
      } catch (err) {
        setError(
          err.response?.data?.detail ||
            "Unable to load ticket history."
        );
      } finally {
        setLoading(false);
      }
    };

    fetchHistory();
  }, [ticketId]);

  const formatLabel = (value) => {
    if (!value) return "Updated";

    return value
      .replaceAll("_", " ")
      .replace(/\b\w/g, (char) => char.toUpperCase());
  };

  const formatDate = (date) => {
    if (!date) return "Not available";

    return new Date(date).toLocaleString();
  };

  const formatValues = (values) => {
    if (!values || Object.keys(values).length === 0) {
      return null;
    }

    return Object.entries(values).map(([key, value]) => (
      <Typography
        key={key}
        variant="body2"
        color="text.secondary"
      >
        {formatLabel(key)}:{" "}
        {typeof value === "object"
          ? JSON.stringify(value)
          : String(value ?? "None")}
      </Typography>
    ));
  };

  return (
    <Paper elevation={2} sx={{ p: { xs: 2, sm: 3 }, mt: 4 }}>
      <Box display="flex" alignItems="center" gap={1} mb={3}>
        <HistoryIcon color="primary" />

        <Typography variant="h5" fontWeight="bold">
          Ticket Activity History
        </Typography>
      </Box>

      {loading ? (
        <Box display="flex" justifyContent="center" py={4}>
          <CircularProgress />
        </Box>
      ) : error ? (
        <Alert severity="error">{error}</Alert>
      ) : history.length === 0 ? (
        <Alert severity="info">
          No activity history available for this ticket yet.
        </Alert>
      ) : (
        <Box>
          {history.map((event, index) => (
            <Box key={event.id}>
              <Box display="flex" gap={2} py={2}>
                <Box
                  sx={{
                    width: 36,
                    height: 36,
                    minWidth: 36,
                    borderRadius: "50%",
                    bgcolor: "primary.light",
                    color: "primary.contrastText",
                    display: "flex",
                    alignItems: "center",
                    justifyContent: "center",
                  }}
                >
                  <HistoryIcon fontSize="small" />
                </Box>

                <Box flex={1}>
                  <Typography fontWeight="bold">
                    {formatLabel(event.event_type)}
                  </Typography>

                  <Typography
                    variant="caption"
                    color="text.secondary"
                  >
                    Actor: {event.actor_id || "System"}
                  </Typography>

                  <Typography
                    variant="caption"
                    display="block"
                    color="text.secondary"
                    mb={1}
                  >
                    {formatDate(event.created_at)}
                  </Typography>

                  {event.old_values &&
                    Object.keys(event.old_values).length > 0 && (
                      <Box mb={1}>
                        <Typography variant="body2" fontWeight="bold">
                          Previous values
                        </Typography>

                        {formatValues(event.old_values)}
                      </Box>
                    )}

                  {event.new_values &&
                    Object.keys(event.new_values).length > 0 && (
                      <Box>
                        <Typography variant="body2" fontWeight="bold">
                          New values
                        </Typography>

                        {formatValues(event.new_values)}
                      </Box>
                    )}
                </Box>
              </Box>

              {index !== history.length - 1 && (
                <Divider />
              )}
            </Box>
          ))}
        </Box>
      )}
    </Paper>
  );
}

export default TicketHistory;
