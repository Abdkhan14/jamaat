import styled from 'styled-components';
import Button from '@mui/material/Button';

export function Header() {
  return (
    <Wrapper>
        <TitleWrapper>
            <Logo src="/mosque.png" height={40} width={60} alt=""/>
            <Title>Jamaat</Title>
        </TitleWrapper>
        <RequestButton variant='outlined'>Request a mosque</RequestButton>
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