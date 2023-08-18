import { StatusOnlineIcon } from "@heroicons/react/outline";
import {
  Card,
  Table,
  TableHead,
  TableRow,
  TableHeaderCell,
  TableBody,
  TableCell,
  Text,
  Title,
  Badge,
} from "@tremor/react";

const data = [
  {
    name: "Viola Amherd",
    Role: "Federal Councillor",
    departement: "The Federal Department of Defence, Civil Protection and Sport (DDPS)",
    status: "active",
  },
  {
    name: "Simonetta Sommaruga",
    Role: "Federal Councillor",
    departement:
      "The Federal Department of the Environment, Transport, Energy and Communications (DETEC)",
    status: "active",
  },
  {
    name: "Alain Berset",
    Role: "Federal Councillor",
    departement: "The Federal Department of Home Affairs (FDHA)",
    status: "active",
  },
  {
    name: "Ignazio Cassis",
    Role: "Federal Councillor",
    departement: "The Federal Department of Foreign Affairs (FDFA)",
    status: "active",
  },
  {
    name: "Ueli Maurer",
    Role: "Federal Councillor",
    departement: "The Federal Department of Finance (FDF)",
    status: "active",
  },
  {
    name: "Guy Parmelin",
    Role: "Federal Councillor",
    departement: "The Federal Department of Economic Affairs, Education and Research (EAER)",
    status: "active",
  },
  {
    name: "Karin Keller-Sutter",
    Role: "Federal Councillor",
    departement: "The Federal Department of Justice and Police (FDJP)",
    status: "active",
  },
];

export default (props) => {
  console.log("log props: ", props.data)
return (
  <Card>
    <Title>Request Logs</Title>
    <Table className="mt-5">
      <TableHead>
        <TableRow>
          <TableHeaderCell>model</TableHeaderCell>
          <TableHeaderCell>request</TableHeaderCell>
          <TableHeaderCell>response</TableHeaderCell>
          <TableHeaderCell>cost per query</TableHeaderCell>
          <TableHeaderCell>response time</TableHeaderCell>
          <TableHeaderCell>project key</TableHeaderCell>
        </TableRow>
      </TableHead>
      <TableBody>
      {props.data && typeof props.data === 'object' && 
        Object.entries(props.data).map(([key, value]) => (
          <TableRow key={key}>
            {console.log(value)}
            <TableCell>{value.model}</TableCell>
            <TableCell>{value.messages.map(item => item.content).join(' ')}</TableCell>
            <TableCell>
              <Text>{value.response.substring(0,50)}</Text>
            </TableCell>
            <TableCell>
              <Text>{value.total_cost.toFixed(5)}</Text>
            </TableCell>
            <TableCell>
              <Text>{value.response_time}</Text>
            </TableCell>
            <TableCell>
              <Text>{value.request_key}</Text>
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  </Card>
)};