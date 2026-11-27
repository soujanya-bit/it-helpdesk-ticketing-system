
import { useState } from "react";
import { useNavigate } from "react-router-dom";

import {
  Alert,
  Box,
  Button,
  Container,
  FormControl,
  InputLabel,
  MenuItem,
  Paper,
  Select,
  TextField,
  Typography,
  CircularProgress,
} from "@mui/material";

import Navbar from "../components/layout/Navbar";
import api from "../api/axios";

function CreateTicket() {
  const navigate = useNavigate();

  const [subject, setSubject] = useState("");
  const [category, setCategory] = useState("general");
  const [description, setDescription] = useState("");
  const [priority, setPriority] = useState("normal");

  const [error, setError] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (event) => {
    event.preventDefault();

    setError("");
    setSubmitting(true);

    try {
      const response = await api.post("/tickets", {
        subject: subject.trim(),
        category: category.trim(),
        description: description.trim(),
        priority,
      });

      navigate(`/tickets/${response.data.id}`);
    } catch (err) {
      const message =
        err.response?.data?.detail ||
        "Unable to create ticket. Please try again.";

      setError(
        typeof message === "string"
          ? message
          : JSON.stringify(message)
      );
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <>
      <Navbar />

      <Container maxWidth="md" sx={{ py: 5 }}>
        <Typography variant="h4" fontWeight="bold" gutterBottom>
          Create Support Ticket
        </Typography>

        <Typography color="text.secondary" mb={4}>
          Describe your IT issue and submit a support request.
        </Typography>

        <Paper elevation={2} sx={{ p: { xs: 3, sm: 4 } }}>
          {error && (
            <Alert severity="error" sx={{ mb: 3 }}>
              {error}
            </Alert>
          )}

          <Box component="form" onSubmit={handleSubmit}>
            <TextField
              label="Ticket Subject"
              fullWidth
              required
              margin="normal"
              value={subject}
              onChange={(event) => setSubject(event.target.value)}
              inputProps={{ minLength: 5, maxLength: 200 }}
              helperText="Enter a short summary of your issue (5–200 characters)."
            />

            <TextField
              label="Category"
              fullWidth
              required
              margin="normal"
              value={category}
              onChange={(event) => setCategory(event.target.value)}
              inputProps={{ minLength: 2, maxLength: 100 }}
              helperText="Examples: hardware, software, network, access."
            />

            <FormControl fullWidth margin="normal">
              <InputLabel id="priority-label">Priority</InputLabel>

              <Select
                labelId="priority-label"
                value={priority}
                label="Priority"
                onChange={(event) => setPriority(event.target.value)}
              >
                <MenuItem value="low">Low</MenuItem>
                <MenuItem value="normal">Normal</MenuItem>
                <MenuItem value="high">High</MenuItem>
                <MenuItem value="urgent">Urgent</MenuItem>
              </Select>
            </FormControl>

            <TextField
              label="Description"
              fullWidth
              required
              multiline
              rows={5}
              margin="normal"
              value={description}
              onChange={(event) =>
                setDescription(event.target.value)
              }
              inputProps={{ minLength: 10 }}
              helperText="Explain the issue, what happened, and any steps you have already tried."
            />

            <Box
              display="flex"
              gap={2}
              justifyContent="flex-end"
              mt={3}
            >
              <Button
                variant="outlined"
                onClick={() => navigate("/dashboard")}
                disabled={submitting}
              >
                Cancel
              </Button>

              <Button
                type="submit"
                variant="contained"
                disabled={submitting}
              >
                {submitting ? (
                  <CircularProgress size={24} color="inherit" />
                ) : (
                  "Submit Ticket"
                )}
              </Button>
            </Box>
          </Box>
        </Paper>
      </Container>
    </>
  );
}

export default CreateTicket;
