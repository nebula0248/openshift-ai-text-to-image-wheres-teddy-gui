import * as React from 'react';
import { ActionGroup, Button, Form, FormGroup, PageSection, TextInput } from '@patternfly/react-core';

import './Dashboard.css';
import { useHistory } from 'react-router-dom';
import { GEN_PHRASE } from '../../constants';

interface PredictionData {
  // your data here
}

const Dashboard: React.FunctionComponent = () => {
  const [entry, setEntry] = React.useState('');
  const history = useHistory();

  const handleEntryChange = (name: string) => {
    setEntry(name);
  };

  async function createPrediction(data: PredictionData): Promise<void> {
    const response = await fetch('/api/predictions', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    });
    if (!response.ok) {
      throw new Error('Network response was not ok.');
    }
    const responseData = await response.json();
    history.push(`/album/${responseData.id}`);
  }

  const onSubmit = async () => {
    console.log('submit');

    try {
      const data: PredictionData = {
        prompt: `${GEN_PHRASE} ${entry}`,
      };
      await createPrediction(data);
    } catch (error) {
      console.error('There was an error!', error);
    }
  };

  return (
    <>
      <PageSection>
        <Form
          onSubmit={(e) => {
            e.preventDefault();
            onSubmit();
          }}
        >
          <FormGroup isRequired fieldId="simple-form-where-01">
            <TextInput
              isRequired
              type="text"
              id="simple-form-name-01"
              name="simple-form-name-01"
              aria-describedby="simple-form-name-01-helper"
              value={entry}
              onChange={handleEntryChange}
            />
          </FormGroup>
          <ActionGroup>
            <Button variant="primary" isDisabled={!entry} onClick={() => onSubmit()}>
              Go!
            </Button>
          </ActionGroup>
        </Form>
      </PageSection>
    </>
  );
};

export { Dashboard };
