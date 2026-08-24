import React, { useState, useEffect } from 'react';
import { loadStripe } from '@stripe/stripe-js';
import {
  Elements,
  CardElement,
  useStripe,
  useElements
} from '@stripe/react-stripe-js';
import { paymentsAPI } from '../services/api';
import { X, CreditCard, Loader } from 'lucide-react';
import toast from 'react-hot-toast';

// Modal do wpłacania na cel oszczędnościowy przez Stripe
const PaymentForm = ({ goal, amount, onSuccess, onClose }) => {
  const stripe = useStripe();
  const elements = useElements();
  const [isProcessing, setIsProcessing] = useState(false);
  const [clientSecret, setClientSecret] = useState(null);
  const [paymentAmount, setPaymentAmount] = useState(amount || '');
  const [isCreatingIntent, setIsCreatingIntent] = useState(false);

  const createPaymentIntent = async () => {
    if (!paymentAmount || Number(paymentAmount) <= 0) {
      toast.error('Podaj prawidłową kwotę');
      return;
    }

    try {
      setIsCreatingIntent(true);
      const { data } = await paymentsAPI.createPaymentForSavingsGoal(
        goal.id,
        Number(paymentAmount)
      );
      setClientSecret(data.client_secret);
      toast.success('Formularz płatności gotowy');
    } catch (error) {
      toast.error(error.response?.data?.error || 'Nie udało się utworzyć płatności');
    } finally {
      setIsCreatingIntent(false);
    }
  };

  const handleSubmit = async (event) => {
    event.preventDefault();

    if (!stripe || !elements || !clientSecret) {
      return;
    }

    setIsProcessing(true);

    const cardElement = elements.getElement(CardElement);

    try {
      const { error: submitError } = await elements.submit();
      if (submitError) {
        toast.error(submitError.message);
        setIsProcessing(false);
        return;
      }

      const { error, paymentIntent } = await stripe.confirmCardPayment(clientSecret, {
        payment_method: {
          card: cardElement,
          billing_details: {
            name: goal.name || 'Płatność na cel oszczędnościowy',
          },
        },
      });

      if (error) {
        toast.error(error.message || 'Płatność nie powiodła się');
        setIsProcessing(false);
      } else if (paymentIntent && paymentIntent.status === 'succeeded') {
        toast.success('Płatność zakończona sukcesem!');
        onSuccess(paymentIntent);
        onClose();
      }
    } catch (err) {
      toast.error('Wystąpił błąd podczas przetwarzania płatności');
      console.error('Payment error:', err);
      setIsProcessing(false);
    }
  };

  const cardElementOptions = {
    style: {
      base: {
        fontSize: '16px',
        color: '#424770',
        '::placeholder': {
          color: '#aab7c4',
        },
      },
      invalid: {
        color: '#9e2146',
      },
    },
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      <div>
        <label className="label">Kwota wpłaty (PLN)</label>
        <input
          type="number"
          step="0.01"
          min="1"
          value={paymentAmount}
          onChange={(e) => {
            const value = e.target.value;
            
            // Walidacja ujemnych kwot
            if (value !== '' && Number(value) < 0) {
              toast.error('Nie można wprowadzić ujemnej kwoty');
              return;
            }
            
            setPaymentAmount(value);
            setClientSecret(null); // Reset gdy zmienia się kwota
          }}
          className="input-field"
          placeholder="0.00"
          required
          disabled={isProcessing || isCreatingIntent}
        />
        {paymentAmount && Number(paymentAmount) > 0 && !clientSecret && (
          <button
            type="button"
            onClick={createPaymentIntent}
            className="mt-2 btn-primary text-sm inline-flex items-center"
            disabled={isProcessing || isCreatingIntent}
          >
            {isCreatingIntent ? (
              <>
                <Loader className="h-4 w-4 mr-2 animate-spin" />
                Przygotowywanie...
              </>
            ) : (
              'Przygotuj płatność'
            )}
          </button>
        )}
      </div>

      {clientSecret && (
        <>
          <div>
            <label className="label mb-2">Dane karty</label>
            <div className="border border-gray-300 rounded-lg p-4 bg-white">
              <CardElement options={cardElementOptions} />
            </div>
          </div>

          <div className="bg-blue-50 border border-blue-200 rounded-lg p-3">
            <p className="text-sm text-blue-800">
              <strong>Cel:</strong> {goal.name}
            </p>
            <p className="text-sm text-blue-800">
              <strong>Kwota:</strong> {Number(paymentAmount).toFixed(2)} PLN
            </p>
          </div>

          <div className="flex gap-3">
            <button
              type="button"
              onClick={onClose}
              className="btn-secondary flex-1"
              disabled={isProcessing}
            >
              Anuluj
            </button>
            <button
              type="submit"
              className="btn-primary flex-1 flex items-center justify-center"
              disabled={!stripe || isProcessing || !clientSecret}
            >
              {isProcessing ? (
                <>
                  <Loader className="h-4 w-4 mr-2 animate-spin" />
                  Przetwarzanie...
                </>
              ) : (
                <>
                  <CreditCard className="h-4 w-4 mr-2" />
                  Zapłać {Number(paymentAmount).toFixed(2)} PLN
                </>
              )}
            </button>
          </div>
        </>
      )}
    </form>
  );
};

const StripePaymentModal = ({ open, onClose, goal, onSuccess }) => {
  const [stripePromise, setStripePromise] = useState(null);
  const [amount, setAmount] = useState('');

  useEffect(() => {
    // Załaduj klucz publiczny Stripe z backendu
    const loadStripeKey = async () => {
      try {
        const { data } = await paymentsAPI.getStripeConfig();
        const stripe = await loadStripe(data.publishable_key);
        setStripePromise(stripe);
      } catch (error) {
        toast.error('Nie udało się załadować konfiguracji Stripe');
        console.error('Stripe config error:', error);
      }
    };

    if (open) {
      loadStripeKey();
      setAmount(''); // Reset kwoty przy otwieraniu
    }
  }, [open]);

  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50">
      <div className="bg-white w-full max-w-lg rounded-lg shadow-strong mx-4">
        <div className="flex items-center justify-between px-6 py-4 border-b">
          <div>
            <h3 className="text-lg font-semibold text-gray-900">Wpłać na cel</h3>
            <p className="text-sm text-gray-500 mt-1">{goal?.name}</p>
          </div>
          <button
            onClick={onClose}
            className="p-1 hover:bg-gray-100 rounded transition-colors"
          >
            <X className="h-5 w-5 text-gray-600" />
          </button>
        </div>

        <div className="p-6">
          {stripePromise ? (
            <Elements stripe={stripePromise}>
              <PaymentForm
                goal={goal}
                amount={amount}
                onSuccess={onSuccess}
                onClose={onClose}
              />
            </Elements>
          ) : (
            <div className="flex items-center justify-center py-8">
              <Loader className="h-6 w-6 animate-spin text-primary-600" />
              <span className="ml-2 text-gray-600">Ładowanie formularza płatności...</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default StripePaymentModal;

