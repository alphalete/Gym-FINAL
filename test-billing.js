#!/usr/bin/env node

// Test the billing functions
const { nextDueDateFromJoin, isOverdue, currentCycleWindow } = require('./billing.js');

console.log('=== Testing Billing Functions ===');

// Test Alice Active (15 days ago)
const aliceJoinDate = new Date(new Date().setDate(new Date().getDate() - 15)).toISOString().slice(0,10);
console.log('Alice Active:');
console.log(`  Join Date: ${aliceJoinDate}`);
console.log(`  Due Date: ${nextDueDateFromJoin(aliceJoinDate)?.toISOString().slice(0,10)}`);
console.log(`  Is Overdue: ${isOverdue(aliceJoinDate)}`);

const aliceCycle = currentCycleWindow(aliceJoinDate);
console.log(`  Current Cycle: ${aliceCycle.start?.toISOString().slice(0,10)} to ${aliceCycle.end?.toISOString().slice(0,10)}`);

console.log('');

// Test Oscar Overdue (45 days ago) 
const oscarJoinDate = new Date(new Date().setDate(new Date().getDate() - 45)).toISOString().slice(0,10);
console.log('Oscar Overdue:');
console.log(`  Join Date: ${oscarJoinDate}`);
console.log(`  Due Date: ${nextDueDateFromJoin(oscarJoinDate)?.toISOString().slice(0,10)}`);
console.log(`  Is Overdue: ${isOverdue(oscarJoinDate)}`);

const oscarCycle = currentCycleWindow(oscarJoinDate);
console.log(`  Current Cycle: ${oscarCycle.start?.toISOString().slice(0,10)} to ${oscarCycle.end?.toISOString().slice(0,10)}`);