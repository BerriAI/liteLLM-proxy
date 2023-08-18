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

const placeholder_data = [
    {
        "name": "krrish@berri.ai",
        "project": "QA App", 
        "total_cost": 100,
        "status": "rate-limited"
    },
    {
        "name": "ishaan@berri.ai",
        "project": "Code Gen Tool", 
        "total_cost": 75,
        "status": "near limit"
    },
    {
        "name": "peter@berri.ai",
        "project": "LLM App Playground", 
        "total_cost": 20,
        "status": "normal"
    }
]

export default (props) => {
    console.log("table props: ", props)
    return (
  <Card>
    <Title>Top Users</Title>
    <Table className="mt-5">
      <TableHead>
        <TableRow>
          <TableHeaderCell>ID</TableHeaderCell>
          <TableHeaderCell>Project</TableHeaderCell>
          <TableHeaderCell>Total Cost</TableHeaderCell>
          <TableHeaderCell>Status</TableHeaderCell>
        </TableRow>
      </TableHead>
      {props.data && typeof props.data === 'object' &&
       <TableBody>
       {Object.entries(placeholder_data).map(([key, value]) => (
        <TableRow key={key}>
            <TableCell>{value.name}</TableCell>
            <TableCell>{value.project}</TableCell>
            <TableCell>{value.total_cost}</TableCell>
            <TableCell>
            {value.status == "rate-limited" ? 
                <Badge color="red">
                    {value.status}
                </Badge>
                : value.status == "near limit" ?
                    <Badge color="orange">
                    {value.status}
                    </Badge>
                    : value.status == "normal" ?
                    <Badge color="blue">
                        {value.status}
                    </Badge>
                    : null
                }
            </TableCell>
        </TableRow>
        ))}
     </TableBody>
} 
    </Table>
  </Card>
)};