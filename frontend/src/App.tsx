import { Description } from "./components/description";
import { Header } from "./components/header"
import styled from 'styled-components';

function App() {

  return (
    <Wrapper>
      <Header/>
      <Description/>
    </Wrapper>
  )
}

const Wrapper = styled.div`
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
`;

export default App
