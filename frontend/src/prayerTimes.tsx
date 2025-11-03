import type { UseQueryResult } from "@tanstack/react-query";
import { Prayer, PRAYER_TIME_KEYS, type PrayerTimes } from "./types";
import { styled } from "styled-components";
import { Alert, CircularProgress, Table, TableBody, TableCell, TableContainer, TableHead, TableRow } from "@mui/material";
import LocationPinIcon from '@mui/icons-material/LocationPin';
import CircleIcon from '@mui/icons-material/Circle';

export function PrayerTimes({
    currentTime,
    prayerTimesResult
}: {
    currentTime: Date,
    prayerTimesResult: UseQueryResult<PrayerTimes[], Error>
}) {
  const {data, isLoading, isError} = prayerTimesResult;

  if(isLoading) {
    return (
        <Wrapper>
            <CircularProgress color="inherit" />
        </Wrapper>
    )
  }

  if(isError) {
    return (
        <Wrapper>
            <Alert severity="error">Failed to load. Try refreshing</Alert>
        </Wrapper>
    );
  }

  return (
    <Wrapper>
        {data?.map(pt => <PrayerTime prayerTime={pt} currentTime={currentTime}/>)}
    </Wrapper>
  )
}

function PrayerTime({prayerTime, currentTime}: {prayerTime: PrayerTimes, currentTime: Date}) {
    return <StyledPaper>
        <Header>
            <MosqueName>{prayerTime.name}</MosqueName>
            <MosqueAddress><StyledLocationPinIcon color="error"/>  <MosqueAddressText>{prayerTime.address}</MosqueAddressText></MosqueAddress>
        </Header>
        <TableContainer>
            <Table size="small" aria-label="simple table">
                <TableHead>
                    <TableRow sx={{borderTop: '1px solid lightgray', backgroundColor: '#f0f0f0'}}>
                        <StyledTableCell>Prayer</StyledTableCell>
                        <StyledTableCell align="right">Begins</StyledTableCell>
                        <StyledTableCell align="right">Jamaat</StyledTableCell>
                        <StyledTableCell align="right">Status</StyledTableCell>
                    </TableRow>
                </TableHead>
                <TableBody>
                {Object.values(Prayer).map((prayer) => {
                    const { start, iqamah } = PRAYER_TIME_KEYS[prayer];
                    const status = getStatus(prayerTime.prayer_times[iqamah], currentTime);

                    return (
                        <TableRow key={prayer}> 
                        <StyledTableCell component="th" scope="row">
                            {prayer}
                        </StyledTableCell>
                        <StyledTableCell align="right">
                            {formatTime(prayerTime.prayer_times[start])}
                        </StyledTableCell>
                        <StyledTableCell align="right">
                            {formatTime(prayerTime.prayer_times[iqamah])}
                        </StyledTableCell>
                        <StyledTableCell align="right">
                            {status === 'available' ?
                                 <Status>
                                    <CircleIcon sx={{fontSize: '12px', color:"green"}} />
                                    Available
                                 </Status> 
                                 : status === 'finished' ? 
                                 <Status>
                                    <CircleIcon sx={{fontSize: '12px', color:"red"}} />
                                    Finished
                                 </Status> :  
                                 <Status>
                                    <CircleIcon sx={{fontSize: '12px', color:"gray"}} />
                                    None
                                 </Status>
                            }
                        </StyledTableCell>
                        </TableRow>
                    );
                })}
                </TableBody>
            </Table>
            </TableContainer>
        <UpdatedAt>Updated At: {formatUpdatedAt(prayerTime.prayer_times.updated_at)}</UpdatedAt>
    </StyledPaper>;
}

function getStatus(iqamah_time: string | null, currentTime: Date): 'available' | 'finished' | 'default'  {
    if (!iqamah_time) return "default";

    // Parse iqamah_time (e.g. "04:59:00" or "4:59 AM")
    const parsed = new Date(`1970-01-01T${iqamah_time}`);
  
    if (isNaN(parsed.getTime())) {
      // Try fallback parse if it's in 12h format with AM/PM
      const tryParse = Date.parse(`1970-01-01 ${iqamah_time}`);
      if (isNaN(tryParse)) return "default";
      return currentTime.getTime() < tryParse ? "available" : "finished";
    }
  
    const current = new Date(
      `1970-01-01T${currentTime.toTimeString().slice(0, 8)}`
    );
  
    return current < parsed ? "available" : "finished"; 
}

function formatTime(time: string | null): string {
    if(!time) {
        return 'None';
    }

    // Create a Date object by attaching an arbitrary date
    const date = new Date(`1970-01-01T${time}`);
    return date.toLocaleTimeString("en-US", {
      hour: "numeric",
      minute: "2-digit",
      hour12: true,
    });
  }

function formatUpdatedAt(updatedAt: string) {
    const date = new Date(updatedAt);

    const options = {
        day: "2-digit",
        month: "2-digit",
        year: "2-digit", 
        hour: "2-digit",
        minute: "2-digit",
        hour12: true,
    } as any;
    
    return new Intl.DateTimeFormat("en-GB", options).format(date);
}

const Status = styled.div`
    display: flex;
    align-items: center;
    justify-content: flex-end;
    gap: 8px;

`;

const UpdatedAt = styled.div`
    font-size: 12px;
    color: gray;
    text-align: center;
    font-style: italic;
    margin-top: 5px;
`;

const MosqueName = styled.div`
    font-size: 20px;
`;

const MosqueAddress = styled.div`
    display: flex;
    justify-content: center;
    align-items: center;
    gap: 3px;
    color: gray;
`;

const MosqueAddressText = styled.div`
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
    max-width: 100%;
    font-size: small;
`;

const StyledLocationPinIcon = styled(LocationPinIcon)({
    transform: 'translateY(-3px)',
  });

const StyledTableCell = styled(TableCell)({
    textTransform: 'capitalize',
    padding: '5px 4px !important',
});

const Header = styled.div`
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    width: 100%;
`;

const StyledPaper = styled.div`
    display: flex;
    flex-direction: column;
    gap: 10px;
    flex: 1;
    max-width: 100%;
    background-color: white;
    color: black;
    padding: 10px;
    border-radius: 4px;
`;

const Wrapper = styled.div`
    display: flex;
    align-items: center;
    gap: 12px;
    justify-content: center;
    flex-wrap: wrap;
    flex: 1;
    width: 100%;
`;
