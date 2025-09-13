'use client';

import React, { useState } from 'react';
import { ChevronLeftIcon, ChevronRightIcon } from '@heroicons/react/24/outline';

interface TourStep {
  id: string;
  title: string;
  description: string;
  content: React.ReactNode;
  icon: string;
}

interface GuidedTourProps {
  steps: TourStep[];
}

export const GuidedTour: React.FC<GuidedTourProps> = ({ steps }) => {
  const [currentStep, setCurrentStep] = useState(0);

  const nextStep = () => {
    if (currentStep < steps.length - 1) {
      setCurrentStep(currentStep + 1);
    }
  };

  const prevStep = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
    }
  };

  const goToStep = (stepIndex: number) => {
    setCurrentStep(stepIndex);
  };

  const currentTourStep = steps[currentStep];

  return (
    <div className="max-w-6xl mx-auto">
      {/* Progress Bar */}
      <div className="mb-8">
        <div className="flex items-center justify-between mb-4">
          <h1 className="text-2xl font-bold text-gray-900">
            Platform Tour & Demo
          </h1>
          <div className="text-sm text-gray-600">
            Step {currentStep + 1} of {steps.length}
          </div>
        </div>
        
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div
            className="bg-blue-600 h-2 rounded-full transition-all duration-300"
            style={{ width: `${((currentStep + 1) / steps.length) * 100}%` }}
          ></div>
        </div>
      </div>

      {/* Step Navigation */}
      <div className="flex flex-wrap gap-2 mb-8">
        {steps.map((step, index) => (
          <button
            key={step.id}
            onClick={() => goToStep(index)}
            className={`px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
              index === currentStep
                ? 'bg-blue-600 text-white'
                : index < currentStep
                ? 'bg-green-100 text-green-800 hover:bg-green-200'
                : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            }`}
          >
            <span className="mr-2">{step.icon}</span>
            {step.title}
          </button>
        ))}
      </div>

      {/* Current Step Content */}
      <div className="bg-white rounded-lg shadow-lg border border-gray-200 overflow-hidden">
        {/* Step Header */}
        <div className="bg-gradient-to-r from-blue-600 to-blue-700 text-white p-6">
          <div className="flex items-center space-x-3">
            <div className="text-3xl">{currentTourStep.icon}</div>
            <div>
              <h2 className="text-2xl font-bold">{currentTourStep.title}</h2>
              <p className="text-blue-100 mt-1">{currentTourStep.description}</p>
            </div>
          </div>
        </div>

        {/* Step Content */}
        <div className="p-6">
          {currentTourStep.content}
        </div>

        {/* Navigation Controls */}
        <div className="bg-gray-50 px-6 py-4 flex items-center justify-between border-t border-gray-200">
          <button
            onClick={prevStep}
            disabled={currentStep === 0}
            className={`flex items-center space-x-2 px-4 py-2 rounded-lg font-medium transition-colors ${
              currentStep === 0
                ? 'text-gray-400 cursor-not-allowed'
                : 'text-gray-700 hover:bg-gray-200'
            }`}
          >
            <ChevronLeftIcon className="w-5 h-5" />
            <span>Previous</span>
          </button>

          <div className="flex space-x-2">
            {steps.map((_, index) => (
              <button
                key={index}
                onClick={() => goToStep(index)}
                className={`w-3 h-3 rounded-full transition-colors ${
                  index === currentStep
                    ? 'bg-blue-600'
                    : index < currentStep
                    ? 'bg-green-500'
                    : 'bg-gray-300'
                }`}
              />
            ))}
          </div>

          <button
            onClick={nextStep}
            disabled={currentStep === steps.length - 1}
            className={`flex items-center space-x-2 px-4 py-2 rounded-lg font-medium transition-colors ${
              currentStep === steps.length - 1
                ? 'text-gray-400 cursor-not-allowed'
                : 'bg-blue-600 text-white hover:bg-blue-700'
            }`}
          >
            <span>{currentStep === steps.length - 1 ? 'Complete' : 'Next'}</span>
            {currentStep < steps.length - 1 && <ChevronRightIcon className="w-5 h-5" />}
          </button>
        </div>
      </div>

      {/* Tour Completion */}
      {currentStep === steps.length - 1 && (
        <div className="mt-8 bg-green-50 border border-green-200 rounded-lg p-6 text-center">
          <div className="text-4xl mb-4">🎉</div>
          <h3 className="text-xl font-bold text-green-900 mb-2">
            Tour Complete!
          </h3>
          <p className="text-green-800 mb-4">
            You&apos;ve explored all the key features of the Ghostworks platform. 
            Ready to start building with AI-native development?
          </p>
          <div className="flex justify-center space-x-4">
            <button
              onClick={() => setCurrentStep(0)}
              className="px-6 py-2 bg-white border border-green-300 text-green-700 rounded-lg hover:bg-green-50 transition-colors"
            >
              Restart Tour
            </button>
            <button
              onClick={() => window.location.href = '/dashboard'}
              className="px-6 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
            >
              Go to Dashboard
            </button>
          </div>
        </div>
      )}
    </div>
  );
};