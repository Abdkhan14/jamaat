import styled from 'styled-components';
import Button from '@mui/material/Button';


export function Description() {
  return (
    <Wrapper>
        <Location>Scarborough - Canada</Location>
        <DescriptionText>All of our neighborhood mosques <br /> in one place</DescriptionText>
        <div>To add your mosque to the list:</div>
        <DescriptionButton variant='contained'>Submit a request</DescriptionButton>
    </Wrapper>
  )
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