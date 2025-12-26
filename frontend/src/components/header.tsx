import styled from 'styled-components';
import Box from '@mui/material/Box';
import Modal from '@mui/material/Modal';
import Button from '@mui/material/Button';
import Typography from '@mui/material/Typography';
import { useState } from 'react';

export function Header() {
  const [open, setOpen] = useState(false);
  const handleOpen = () => setOpen(true);
  const handleClose = () => setOpen(false);

  return (
    <Wrapper>
        <TitleWrapper>
            <Logo src="/mosque.png" height={40} width={60} alt=""/>
            <Title>Jamaat</Title>
        </TitleWrapper>
        <RequestButton variant='outlined' onClick={handleOpen}>About</RequestButton>
        <Modal
        keepMounted
        open={open}
        onClose={handleClose}
        aria-labelledby="keep-mounted-modal-title"
        aria-describedby="keep-mounted-modal-description"
      >
        <Box sx={{
          position: 'absolute',
          top: '50%',
          left: '50%',
          transform: 'translate(-50%, -50%)',
          bgcolor: 'background.paper',
          border: '2px solid #000',
          boxShadow: 24,
          p: 3,
          width: '60%',
          borderRadius: '10px',
        }}>
          <Typography fontSize={16} style={{color: 'black'}} id="keep-mounted-modal-title" variant="h6" component="h2">
            Hi! I'm Mohammed. I'm a software engineer, but first and foremost a Muslim.
            <br />
            <br />
            I built this website to help my community easily access prayer times for their mosques in one place, without the need to visit multiple sites.
            <br />
            <br />
            If you have any questions or feedback, please feel free to contact me at <a href="mailto:mohammed@jamaat.ca">abdullahibnekhan@gmail.com</a>, or
            connect with me on <a href='https://www.linkedin.com/in/abdullahkhanibne/'>LinkedIn</a>.
            <br />
            <br />
            Thank you for using Jamaat!
          </Typography>
        </Box>
      </Modal>
    </Wrapper>
  )
};

const Logo = styled.img`
   transform: translateY(-3px);
`;

const Title = styled.h1`
   padding: 0;
   margin: 0;
`;

const TitleWrapper = styled.div`
  display: flex;
  align-items: center;
`;

const Wrapper = styled.div`
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
`;

const RequestButton = styled(Button)({
    boxShadow: 'none',
    textTransform: 'none',
    fontSize: 16,
    padding: '6px 12px',
    border: '2px solid #6673bc !important',
    lineHeight: 1.5,
    borderRadius: '8px',
    fontFamily: 'var(--font-primary) !important',
    color: 'var(--primary-text-color) !important',
    '&:hover': {
      backgroundColor: 'var(--primary-text-color)',
      color: 'black !important',
      boxShadow: 'none',
    },
  });