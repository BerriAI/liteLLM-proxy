'use client'
import Link from 'next/link';
import Image from 'next/image'
import React, { useState } from 'react';
function Navbar() {
    return (
        <nav className="left-0 right-0 top-0 flex justify-between items-center h-12">
            <div className="text-left mx-4 my-2 absolute top-0 left-0 text-gray-800 text-4xl">
            <div className="flex flex-col items-center">
                <button className="text-gray-800 text-2xl px-4 py-1 rounded text-center">🚅 LiteLLM Proxy Server</button>
                <a href="https://railway.app">
                <Image src="https://railway.app/button.svg" alt="Powered by Railway" width={200} height={30} />
                </a>
            </div>
            </div>
            <div className="text-right mx-4 my-2 absolute top-0 right-0">
                <a href="https://github.com/BerriAI/litellm/issues/new" target="_blank" rel="noopener noreferrer">
                    <button className="border border-gray-800 rounded-lg text-gray-800 text-xl px-4 py-1 rounded p-1 mr-1 text-center">+Add new Key</button>
                </a>
                <a href="https://github.com/BerriAI/litellm/issues/new" target="_blank" rel="noopener noreferrer">
                    <button className="border border-gray-800 rounded-lg text-gray-800 text-xl px-4 py-1 rounded p-1 mr-1 text-center">+Add new LLM</button>
                </a>
                <a href="https://github.com/BerriAI/litellm/issues/new" target="_blank" rel="noopener noreferrer">
                    <button className="border border-gray-800 rounded-lg text-gray-800 text-xl px-4 py-1 rounded p-1 text-center">Send data to Sentry, PostHog, etc.</button>
                </a>
            </div>
        </nav>
    )
}

export default Navbar;