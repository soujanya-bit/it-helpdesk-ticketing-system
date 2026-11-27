
import { useEffect, useState } from "react";

import {
  Alert,
  Box,
  Card,
  CardContent,
  CircularProgress,
  Container,
  Grid,
  Typography,
} from "@mui/material";

import Navbar from "../components/layout/Navbar";
import api from "../api/axios";

const STATUSES = [
  { label: "Total Tickets", value: "all" },
  { label: "Open", value: "open" },
  { label: "In Progress", value: "in_progress" },
  { label: "Resolved", value: "resolved" },
];

function Dashboard() {
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
          "Unable to load your tickets."
        );
      } finally {
        setLoading(false);
      }
    };

    fetchTickets();
  }, []);

  const getTicketCount = (status) => {
    if (status === "all") {
      return tickets.length;
    }

    return tickets.filter(
      (ticket) => ticket.status === status
    ).length;
  };

  return (
    <>
      <Navbar />

      <Container maxWidth="lg" sx={{ py: 5 }}>
        <Typography variant="h4" fontWeight="bold" gutterBottom>
          Dashboard
        </Typography>

        <Typography color="text.secondary" mb={4}>
          Overview of your IT support tickets.
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
              {STATUSES.map((stat) => (
                <Grid key={stat.value} size={{ xs: 12, sm: 6, md: 3 }}>
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
                        {getTicketCount(stat.value)}
                      </Typography>
                    </CardContent>
                  </Card>
                </Grid>
              ))}
            </Grid>

            <Box mt={5}>
              <Typography variant="h5" fontWeight="bold" mb={2}>
                Recent Tickets
              </Typography>

              {tickets.length === 0 ? (
                <Alert severity="info">
                  You haven't created any support tickets yet.
                </Alert>
              ) : (
                <Box display="flex" flexDirection="column" gap={2}>
                  {tickets.slice(0, 5).map((ticket) => (
                    <Card key={ticket.id} variant="outlined">
                      <CardContent>
                        <Typography fontWeight="bold">
                          {ticket.subject}
                        </Typography>

                        <Typography
                          variant="body2"
                          color="text.secondary"
                          sx={{ mt: 1 }}
                        >
                          Status: {ticket.status.replaceAll("_", " ")}
                          {" | "}
                          Priority: {ticket.priority}
                        </Typography>
                      </CardContent>
                    </Card>
                  ))}
                </Box>
              )}
            </Box>
          </>
        )}
      </Container>
    </>
  );
}

export default Dashboard;
