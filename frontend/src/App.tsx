import { Description } from "./components/description";
import { Header } from "./components/header"
import styled from 'styled-components';
import { usePrayerTimes } from "./hooks/usePrayerTimes";
import { PrayerTimes } from "./prayerTimes";
import { useCurrentTime } from "./hooks/useCurrentTime";

function App() {
  const prayerTimesResult = usePrayerTimes();
  const currentTime = useCurrentTime();

  return (
    <Wrapper>
      <Header/>
      <Description/>
      <PrayerTimes currentTime={currentTime} prayerTimesResult={prayerTimesResult}/>
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
