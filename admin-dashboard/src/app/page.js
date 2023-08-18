"use client"
import React, { useEffect, useState } from 'react';
import Image from 'next/image'
import Navbar from './components/Navbar';
import Table from './components/Table';
import Logs from './components/Logs';
import { BadgeDelta, Card, Col, Grid, DeltaType, Flex, Metric, ProgressBar, Text } from "@tremor/react";
import { Title, LineChart, BarChart} from "@tremor/react";

const spend_per_project = [
  {
    "spend": 1000,
    "project": "QA App",
  }, 
  {
    "spend": 500,
    "project": "LLM App Playground"
  },
  {
    "spend": 1500,
    "project": "Code Gen Tool"
  }
]

export default function Home() {
  const [data, setData] = useState([]);

  useEffect(() => {
      // call your API route to fetch the data
      fetch('/api/')
          .then(res => res.json())
          .then(resData => setData(resData))
  }, []);

  return (
    <main className="flex min-h-screen flex-col items-center justify-between p-10">
    <Navbar />
    <div className="fixed before:h-[300px] before:w-[480px] before:-translate-x-1/2 before:rounded-full before:bg-gradient-radial before:from-white before:to-transparent before:blur-2xl before:content-[''] after:absolute after:-z-20 after:h-[180px] after:w-[240px] after:translate-x-1/3 after:bg-gradient-conic after:from-sky-200 after:via-blue-200 after:blur-2xl after:content-[''] before:dark:bg-gradient-to-br before:dark:from-transparent before:dark:to-blue-700 before:dark:opacity-10 after:dark:from-sky-900 after:dark:via-[#0141ff] after:dark:opacity-40 before:lg:h-[360px] z-[-1]"/>
    <Grid numItemsLg={2} className="mt-6 gap-6">
    <Card>
    <Title className='mb-3'>Spend per project</Title>
    <Text>Total Spend</Text>
    <Metric>$ 3000</Metric>
    <BarChart
      className="mt-6"
      data={spend_per_project}
      index="project"
      categories={["spend"]}
      colors={["emerald"]}
      yAxisWidth={40}
    />
  </Card>
  {data && <Table data={data["spend_per_key"]}/>}
  <Col numColSpan={1} numColSpanLg={2}>
  {data && <Logs data={data["logs"]}/>}
  </Col>
    </Grid>
    </main>
  )
}