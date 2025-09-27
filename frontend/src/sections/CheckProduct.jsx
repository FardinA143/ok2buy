import React, { useState } from 'react';
import { Github } from 'lucide-react';

const required_fields = [
  'product_code',
  'product_name',
  'product_description',
  'shop',
  'status',
  'laws',
];

const handleScrollToAbout = () => {
  const aboutSection = document.getElementById('about');
  if (aboutSection) {
    aboutSection.scrollIntoView({ behavior: 'smooth' });
  }
};

const LoadingOverlay = () => {
  return (
    <div className="fixed inset-0 flex items-center justify-center bg-gray-200 bg-opacity-60 backdrop-blur-sm z-50">
      <div className="w-16 h-16 border-4 border-primary border-t-transparent rounded-full animate-spin"></div>
    </div>
  );
};

const CheckProduct = () => {
  const [productId, setProductId] = useState('');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const renderProductDescription = (descriptionArray) => {
    if (!Array.isArray(descriptionArray) || descriptionArray.length === 0) {
      return (
        <div className="mb-4">
          <strong className="capitalize text-gray-700 block mb-2">
            Product Description:
          </strong>
          <span className="text-gray-600">No description available</span>
        </div>
      );
    }

    return (
      <div className="mb-4">
        <strong className="capitalize text-gray-700 block mb-3">
          Product Description:
        </strong>
        <div className="ml-4 space-y-2 bg-gray-50 p-4 rounded-lg">
          {descriptionArray.map((itemArray, idx) => {
            const item =
              Array.isArray(itemArray) && itemArray.length > 0
                ? itemArray[0]
                : itemArray;

            return item && item.key && item.values ? (
              <div key={idx} className="flex flex-wrap items-start gap-2">
                <span className="font-medium text-gray-800 min-w-fit">
                  {item.key}:
                </span>
                <span className="text-gray-600 flex-1">
                  {Array.isArray(item.values)
                    ? item.values.join(', ')
                    : item.values}
                </span>
              </div>
            ) : null;
          })}
        </div>
      </div>
    );
  };

  const handleCheck = async () => {
    try {
      if (!productId.trim()) {
        throw new Error('Product ID cannot be empty');
      }
      if (isNaN(productId)) {
        throw new Error('Product ID must be a number');
      }

      const res = await fetch(
        `https://ok2buy.onrender.com/checkproductsapi/product/${productId}`
      );

      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.detail || 'Failed to fetch product info');
      }
      setResult({ data });
    } catch (err) {
      console.error('Error fetching:', err);
      setResult({ error: err.message });
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status) => {
    switch (status.toLowerCase()) {
      case 'legal':
        return 'bg-green-600';
      case 'permit_or_registration':
        return 'bg-yellow-500';
      case 'illegal':
        return 'bg-red-600';
      default:
        return 'bg-gray-500';
    }
  };

  const renderResult = (response) => {
    if (response.error) {
      let colorClass = 'text-red-600';
      if (response.error.includes('404')) colorClass = 'text-blue-600';
      if (response.error.toLowerCase().includes('failed'))
        colorClass = 'text-black';

      return (
        <div
          className={`mt-6 p-4 border ${colorClass} bg-red-100 rounded-lg text-center`}
        >
          <strong>Error:</strong> {response.error}
        </div>
      );
    }

    const data = response.data;

    return (
      <div className="mt-6 p-8 bg-background shadow-xl rounded-2xl w-full">
        <h2 className="text-2xl font-bold mb-6 text-center text-gray-800">
          Product Details
        </h2>
        {required_fields.map((field) => {
          const fieldValue = data[field];
          if (!fieldValue) return null;

          if (field === 'product_description' && Array.isArray(fieldValue)) {
            return renderProductDescription(fieldValue);
          }

          if (field === 'status') {
            let statusColor = 'text-gray-700';
            if (fieldValue.toLowerCase() === 'legal')
              statusColor = 'text-green-600';
            if (fieldValue.toLowerCase() === 'permit_or_registration')
              statusColor = 'text-yellow-600';
            if (fieldValue.toLowerCase() === 'illegal')
              statusColor = 'text-red-600';

            return (
              <div key={field} className="flex items-center gap-2 mb-4">
                <strong className="capitalize text-gray-700">
                  {field.replace('_', ' ')}:
                </strong>
                <span
                  className={`px-3 py-1 rounded-full text-white font-semibold ${getStatusColor(
                    fieldValue
                  )}`}
                >
                  {fieldValue}
                </span>
              </div>
            );
          }
          // Laws array
          if (field === 'laws' && Array.isArray(fieldValue)) {
            return (
              <div key={field} className="mb-4">
                <strong className="capitalize text-gray-700">Reasoning:</strong>{' '}
                <span className="text-gray-600">{fieldValue.join(', ')}</span>
              </div>
            );
          }

          return (
            <div key={field} className="mb-4">
              <strong className="capitalize text-gray-700">
                {field.replace('_', ' ')}:
              </strong>{' '}
              <span className="text-gray-600">{fieldValue}</span>
            </div>
          );
        })}
      </div>
    );
  };

  return (
    <div className="flex flex-col items-center min-h-screen bg-background px-4 py-12">
      {loading && <LoadingOverlay />}
      <div className="w-full max-w-4xl flex flex-col items-center">
        {/* Title */}
        <h1 className="text-5xl font-bold mb-4 text-center text-foreground">
          ok2buy
        </h1>

        <p className="text-lg text-gray-600 mb-10 text-center max-w-2xl">
          Enter a product ID to check if the product is{' '}
          <span className="font-semibold">legal</span>,{' '}
          <span className="font-semibold">illegal</span>, or requires{' '}
          <span className="font-semibold">permit/registration</span> in
          Switzerland.
        </p>

        <div className="flex w-full mb-6 ">
          <input
            type="text"
            placeholder="🔍 Enter product ID..."
            value={productId}
            onChange={(e) => setProductId(e.target.value)}
            className="flex-1 px-4 py-3 border rounded-l-xl focus:outline-none focus:ring-2 focus:ring-primary text-gray-700"
          />
          <button
            onClick={() => {
              setResult('');
              setLoading(true);
              handleCheck();
            }}
            className="px-6 py-3 bg-primary text-white rounded-r-xl hover:bg-primary font-semibold"
          >
            Search
          </button>
        </div>

        {result && renderResult(result)}
      </div>
      <div className="mt-12 flex items-center justify-center gap-4 mb-8">
        <button
          onClick={handleScrollToAbout}
          title="About Section"
          className="px-6 py-3 bg-primary text-white rounded-full hover:bg-white hover:text-primary border-2 border-primary transition-colors duration-300"
        >
          About
        </button>
        <a
          href="https://github.com/FardinA143/ok2buy"
          target="_blank"
          rel="noopener noreferrer"
          title="GitHub Repository"
          className="w-12 h-12 flex items-center justify-center bg-primary text-white rounded-full hover:bg-white hover:text-primary border-2 border-primary transition-colors duration-300"
        >
          <Github size={24} />
        </a>
      </div>
    </div>
  );
};

export default CheckProduct;
