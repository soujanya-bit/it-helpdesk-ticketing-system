
import { useCallback, useEffect, useState } from "react";

import {
  Alert,
  Box,
  Button,
  Chip,
  CircularProgress,
  Divider,
  Paper,
  TextField,
  Typography,
  Checkbox,
  FormControlLabel,
} from "@mui/material";

import SendIcon from "@mui/icons-material/Send";

import api from "../../api/axios";
import { useAuth } from "../../context/AuthContext";

function Comments({ ticketId }) {
  const { user } = useAuth();

  const [comments, setComments] = useState([]);
  const [body, setBody] = useState("");
  const [isInternal, setIsInternal] = useState(false);

  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");

  const canAddInternalNotes =
    user?.role === "agent" || user?.role === "admin";

  const fetchComments = useCallback(async () => {
    try {
      setError("");

      const response = await api.get(
        `/tickets/${ticketId}/comments`
      );

      setComments(response.data);
    } catch (err) {
      setError(
        err.response?.data?.detail ||
        "Unable to load comments."
      );
    } finally {
      setLoading(false);
    }
  }, [ticketId]);

  useEffect(() => {
    fetchComments();
  }, [fetchComments]);

  const handleSubmit = async (event) => {
    event.preventDefault();

    const trimmedBody = body.trim();

    if (!trimmedBody) {
      setError("Please enter a comment.");
      return;
    }

    if (trimmedBody.length > 5000) {
      setError("Comments cannot exceed 5000 characters.");
      return;
    }

    setSubmitting(true);
    setError("");

    try {
      const endpoint = isInternal
        ? `/tickets/${ticketId}/internal-notes`
        : `/tickets/${ticketId}/comments`;

      await api.post(endpoint, {
        body: trimmedBody,
      });

      setBody("");
      setIsInternal(false);

      await fetchComments();
    } catch (err) {
      setError(
        err.response?.data?.detail ||
        "Unable to submit your comment."
      );
    } finally {
      setSubmitting(false);
    }
  };

  const formatDate = (date) => {
    return new Date(date).toLocaleString();
  };

  return (
    <Paper elevation={2} sx={{ p: { xs: 2, sm: 3 }, mt: 4 }}>
      <Typography variant="h5" fontWeight="bold" mb={3}>
        Comments & Discussion
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {loading ? (
        <Box display="flex" justifyContent="center" py={4}>
          <CircularProgress />
        </Box>
      ) : comments.length === 0 ? (
        <Alert severity="info" sx={{ mb: 3 }}>
          No comments yet. Start the conversation below.
        </Alert>
      ) : (
        <Box display="flex" flexDirection="column" gap={2} mb={3}>
          {comments.map((comment) => (
            <Box
              key={comment.id}
              sx={{
                p: 2,
                borderRadius: 2,
                border: "1px solid",
                borderColor: "divider",
                bgcolor: comment.is_internal
                  ? "warning.50"
                  : "background.paper",
              }}
            >
              <Box
                display="flex"
                justifyContent="space-between"
                alignItems="center"
                flexWrap="wrap"
                gap={1}
                mb={1}
              >
                <Typography variant="body2" fontWeight="bold">
                  Author: {comment.author_id.slice(0, 8)}
                </Typography>

                <Box display="flex" gap={1} alignItems="center">
                  {comment.is_internal && (
                    <Chip
                      label="Internal Note"
                      color="warning"
                      size="small"
                    />
                  )}

                  <Typography
                    variant="caption"
                    color="text.secondary"
                  >
                    {formatDate(comment.created_at)}
                  </Typography>
                </Box>
              </Box>

              <Divider sx={{ mb: 1 }} />

              <Typography
                variant="body1"
                sx={{ whiteSpace: "pre-wrap" }}
              >
                {comment.body}
              </Typography>
            </Box>
          ))}
        </Box>
      )}

      <Divider sx={{ my: 3 }} />

      <Typography variant="h6" fontWeight="bold" mb={2}>
        Add a Comment
      </Typography>

      <Box component="form" onSubmit={handleSubmit}>
        <TextField
          label="Write your comment"
          fullWidth
          multiline
          rows={4}
          required
          value={body}
          onChange={(event) => setBody(event.target.value)}
          inputProps={{ maxLength: 5000 }}
          helperText={`${body.length}/5000 characters`}
        />

        {canAddInternalNotes && (
          <FormControlLabel
            sx={{ mt: 1 }}
            control={
              <Checkbox
                checked={isInternal}
                onChange={(event) =>
                  setIsInternal(event.target.checked)
                }
              />
            }
            label="Add as an internal note"
          />
        )}

        <Box display="flex" justifyContent="flex-end" mt={2}>
          <Button
            type="submit"
            variant="contained"
            endIcon={<SendIcon />}
            disabled={submitting || !body.trim()}
          >
            {submitting ? (
              <CircularProgress size={22} color="inherit" />
            ) : (
              "Submit Comment"
            )}
          </Button>
        </Box>
      </Box>
    </Paper>
  );
}

export default Comments;
