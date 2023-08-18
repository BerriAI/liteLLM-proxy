// app/api/route.js 👈🏽

import { NextResponse } from 'next/server'
import fs from 'fs';
import path from 'path';

export async function GET(req, res) {
  // Specify the path to your JSON file
  const filepath = path.resolve(process.cwd(), '../', 'request_logs.json');

  try {
    // Read the file synchronously
    const rawJsonData = fs.readFileSync(filepath, 'utf8');

    // Parse the file to a JavaScript Object
    const jsonData = JSON.parse(rawJsonData);
    const finalResponse = {}
    const transformedData = [];
    let total_cost = 0
    let spend_per_key = {}
    for (const [key, value] of Object.entries(jsonData._default)) {
        total_cost += value.total_cost
        if (!spend_per_key.hasOwnProperty(value.request_key)) {
            // Create a new key-value pair
            let new_key = value.request_key
            spend_per_key[new_key] = value.total_cost;
        } else {
            let new_key = value.request_key
            spend_per_key[new_key] += value.total_cost;
        }

        let date = new Date(value.created_at*1000);
     
        // Format the date into YYYY-MM-DD
        let formattedDate = `${date.getFullYear()}-${('0' + (date.getMonth()+1)).slice(-2)}-${('0' + date.getDate()).slice(-2)}`;
     
        // Extract the hours, minutes, and day of the week from the date
        let hours = date.getHours();
        let minutes = date.getMinutes();
        let dayOfWeek = date.getDay();
     
        // Find index of specific object
        var foundIndex = transformedData.findIndex(x => x.time == formattedDate && x.hours == hours && x.minutes == minutes && x.dayOfWeek == dayOfWeek);
     
        if (foundIndex === -1) {
          transformedData.push({
                time: formattedDate,
                hours: hours,
                minutes: minutes,
                dayOfWeek: dayOfWeek,
                'number of requests': 1 // logging for each request in our logs
            });
        } else {
          transformedData[foundIndex]['number of requests']++;
        }
    }
    
    
    
    console.log("transformedData: ", transformedData)
    finalResponse["daily_requests"] = transformedData
    finalResponse["total_cost"] = total_cost
    finalResponse["spend_per_key"] = spend_per_key
    finalResponse["logs"] =  Object.values(jsonData._default);
    console.log("finalResponse: ", finalResponse)
    // Return the processed data in the API response
    return NextResponse.json(finalResponse)
    res.status(200).json(transformedData);
  } catch (err) {
    console.error("Failed to load or process file: ", err);
    Response('Error reading data', {status: 500})
  }
}