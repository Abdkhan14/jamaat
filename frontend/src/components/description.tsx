import styled from 'styled-components';
import Button from '@mui/material/Button';
import Modal from '@mui/material/Modal';
import Box from '@mui/material/Box';
import TextField from '@mui/material/TextField';
import Typography from '@mui/material/Typography';
import IconButton from '@mui/material/IconButton';
import CloseIcon from '@mui/icons-material/Close';
import Snackbar from '@mui/material/Snackbar';
import Alert from '@mui/material/Alert';
import { useState } from 'react';

export function Description() {
  const [open, setOpen] = useState(false);
  const [mosqueName, setMosqueName] = useState('');
  const [additionalInfo, setAdditionalInfo] = useState('');
  const [showToast, setShowToast] = useState(false);

  const handleOpen = () => setOpen(true);
  const handleClose = () => {
    setOpen(false);
    setMosqueName('');
    setAdditionalInfo('');
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    // Handle form submission here
    console.log({ mosqueName, additionalInfo });
    handleClose();
    setShowToast(true);
  };

  const handleCloseToast = () => {
    setShowToast(false);
  };

  return (
    <Wrapper>
      <Location>Scarborough - Canada</Location>
      <DescriptionText>All of our neighborhood mosques <br /> in one place</DescriptionText>
      <div>To add your mosque to the list:</div>
      <DescriptionButton variant='contained' onClick={handleOpen}>
        Submit a request
      </DescriptionButton>

      <Modal
        open={open}
        onClose={handleClose}
        aria-labelledby="mosque-request-modal"
      >
        <ModalBox>
          <ModalHeader>
            <Typography id="mosque-request-modal" variant="h6" component="h2">
              Submit Mosque Request
            </Typography>
            <IconButton onClick={handleClose} size="small">
              <CloseIcon />
            </IconButton>
          </ModalHeader>

          <form onSubmit={handleSubmit}>
            <FormContent>
              <TextField
                required
                fullWidth
                label="Mosque Name"
                value={mosqueName}
                onChange={(e) => setMosqueName(e.target.value)}
                variant="outlined"
              />

              <TextField
                fullWidth
                label="Additional Information"
                placeholder="Include website URL, location details, or any other relevant information..."
                value={additionalInfo}
                onChange={(e) => setAdditionalInfo(e.target.value)}
                variant="outlined"
                multiline
                rows={4}
              />

              <ButtonGroup>
                <CancelButton onClick={handleClose}>
                  Cancel
                </CancelButton>
                <SubmitButton type="submit" variant="contained">
                  Submit Request
                </SubmitButton>
              </ButtonGroup>
            </FormContent>
          </form>
        </ModalBox>
      </Modal>

      <Snackbar 
        open={showToast} 
        autoHideDuration={4000} 
        onClose={handleCloseToast}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert 
          onClose={handleCloseToast} 
          severity="success" 
          sx={{ width: '100%' }}
        >
          Request submitted successfully!
        </Alert>
      </Snackbar>
    </Wrapper>
  );
}

const Location = styled.div`
  text-transform: uppercase;
  font-family: var(--font-secondary);
`;

const DescriptionText = styled.div`
  font-family: var(--font-secondary);
  font-size: clamp(1.5rem, 5vw, 4rem);
  text-align: center;
  width: 100%;
`;

const Wrapper = styled.div`
  display: flex;
  flex-direction: column;
  gap: 10px;
  align-items: center;
  justify-content: center;
  width: 100%;
  margin: 40px;
`;

const DescriptionButton = styled(Button)({
  marginTop: '8px !important',
  backgroundColor: 'white !important',
  textTransform: 'none',
  fontSize: 16,
  lineHeight: 1.5,
  borderRadius: '8px',
  fontFamily: 'var(--font-primary) !important',
  color: 'black !important',
  '&:hover': {
    boxShadow: 'none',
  },
});

const ModalBox = styled(Box)`
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 80vw;
  max-width: 500px;
  background-color: white;
  border-radius: 8px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
  padding: 24px;

  @media (max-width: 600px) {
    padding: 20px;
  }
`;

const ModalHeader = styled.div`
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;

  h2 {
    font-family: var(--font-secondary);
    margin: 0;
  }
`;

const FormContent = styled.div`
  display: flex;
  flex-direction: column;
  gap: 20px;
`;

const ButtonGroup = styled.div`
  display: flex;
  gap: 12px;
  justify-content: flex-end;
  margin-top: 8px;

  @media (max-width: 600px) {
    flex-direction: column-reverse;
  }
`;

const CancelButton = styled(Button)`
  text-transform: none !important;
  color: #666 !important;
  font-family: var(--font-primary) !important;

  @media (max-width: 600px) {
    width: 100%;
  }
`;

const SubmitButton = styled(Button)`
  text-transform: none !important;
  background-color: black !important;
  font-family: var(--font-primary) !important;

  @media (max-width: 600px) {
    width: 100%;
  }
`;