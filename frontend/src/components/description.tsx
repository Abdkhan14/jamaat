import styled from 'styled-components';
import Button from '@mui/material/Button';


export function Description() {
  return (
    <Wrapper>
        <Location>Scarborough - Canada</Location>
        <DescriptionText>All of our neighborhood mosques <br /> in one place</DescriptionText>
        <div>To get notified about changes in prayer times:</div>
        <DescriptionButton variant='contained'>Subscribe</DescriptionButton>
    </Wrapper>
  )
}

const Location = styled.div`
    text-transform: uppercase;
    font-family: var(--font-secondary);
`;

const DescriptionText = styled.div`
    font-family: var(--font-secondary);
    font-size: 60px;
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
  margin: 50px;
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