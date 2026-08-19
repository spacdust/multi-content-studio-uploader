import React from 'react';
import { useToast } from './hooks/useToast';
import { useSettings } from './hooks/useSettings';
import { useAccounts } from './hooks/useAccounts';
import { useContent } from './hooks/useContent';

import Toast from './components/common/Toast';
import Navbar from './components/navbar/Navbar';
import FeedHeader from './components/feed/FeedHeader';
import FeedFilterBar from './components/feed/FeedFilterBar';
import ContentFeedList from './components/feed/ContentFeedList';
import StudioInspector from './components/inspector/StudioInspector';

import AccountManagerModal from './components/modals/AccountManagerModal';
import AddMediaModal from './components/modals/AddMediaModal';
import AddDateModal from './components/modals/AddDateModal';
import SettingsModal from './components/modals/SettingsModal';
import DeleteConfirmModal from './components/modals/DeleteConfirmModal';

export default function App() {
  const { toast, showToast } = useToast();

  const settingsState = useSettings(showToast);
  const accountsState = useAccounts(showToast);
  const contentState = useContent(
    accountsState.selectedAccount,
    accountsState.currentAccData,
    showToast,
    accountsState.setShowAccountManagerModal
  );

  return (
    <div className="min-h-screen bg-[#09090b] text-[#f4f4f5] flex flex-col antialiased selection:bg-emerald-500 selection:text-black">
      {/* Toast Notification Alert */}
      <Toast toast={toast} />

      {/* Pro Studio Header & Navigation */}
      <Navbar
        llmModel={settingsState.llmModel}
        accounts={accountsState.accounts}
        selectedAccount={accountsState.selectedAccount}
        currentAccData={accountsState.currentAccData}
        isAccountDropdownOpen={accountsState.isAccountDropdownOpen}
        setIsAccountDropdownOpen={accountsState.setIsAccountDropdownOpen}
        handleAccountChange={accountsState.handleAccountChange}
        setShowAccountManagerModal={accountsState.setShowAccountManagerModal}
        handleOpenTikTokStudioBrowser={accountsState.handleOpenTikTokStudioBrowser}
        handleOpenInstagramBrowser={accountsState.handleOpenInstagramBrowser}
        handleOpenFacebookBrowser={accountsState.handleOpenFacebookBrowser}
        setShowSettingsModal={settingsState.setShowSettingsModal}
        setTestResult={settingsState.setTestResult}
        showToast={showToast}
      />

      {/* Main Studio 2-Pane Master Detail Layout */}
      <main className="flex-1 max-w-[1600px] w-full mx-auto p-6 grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">
        {/* Left Pane: Master Feed & Timeline List (7 cols) */}
        <section className="lg:col-span-7 flex flex-col gap-4">
          <FeedHeader
            itemCount={contentState.sortedItems.length}
            setSingleMediaFile={contentState.setSingleMediaFile}
            setSingleMediaPreviewUrl={contentState.setSingleMediaPreviewUrl}
            setCarouselSlides={contentState.setCarouselSlides}
            setIsScheduledUpload={contentState.setIsScheduledUpload}
            setUploadScheduleTime={contentState.setUploadScheduleTime}
            setUploadDate={contentState.setUploadDate}
            setShowUploadModal={contentState.setShowUploadModal}
          />

          <FeedFilterBar
            filterCategory={contentState.filterCategory}
            setFilterCategory={contentState.setFilterCategory}
            filterDate={contentState.filterDate}
            setFilterDate={contentState.setFilterDate}
            filterStatus={contentState.filterStatus}
            setFilterStatus={contentState.setFilterStatus}
            sortBy={contentState.sortBy}
            setSortBy={contentState.setSortBy}
            availableDates={contentState.availableDates}
            setShowAddDateModal={contentState.setShowAddDateModal}
          />

          <ContentFeedList
            items={contentState.sortedItems}
            loadingContent={contentState.loadingContent}
            selectedItemKey={contentState.selectedItemKey}
            onSelectItem={contentState.setSelectedItemKey}
            filterDate={contentState.filterDate}
            setFilterDate={contentState.setFilterDate}
            onDeleteClick={(item) => {
              contentState.setItemToDelete(item);
              contentState.setShowDeleteConfirmModal(true);
            }}
          />
        </section>

        {/* Right Pane: Studio Inspector (5 cols) */}
        <StudioInspector
          selectedItem={contentState.selectedItem}
          currentEdit={contentState.currentEdit}
          isInspectorScheduled={contentState.isInspectorScheduled}
          currentHashtags={contentState.currentHashtags}
          carouselSlideIndices={contentState.carouselSlideIndices}
          setCarouselSlideIndices={contentState.setCarouselSlideIndices}
          setEditedItems={contentState.setEditedItems}
          generatingCaption={contentState.generatingCaption}
          handleGenerateCaption={contentState.handleGenerateCaption}
          handleSaveCaption={contentState.handleSaveCaption}
          uploadingItem={contentState.uploadingItem}
          isPublishDisabled={contentState.isPublishDisabled}
          publishBtnText={contentState.publishBtnText}
          activePlatforms={contentState.activePlatforms}
          currentAccData={accountsState.currentAccData}
          handleUploadItem={contentState.handleUploadItem}
        />
      </main>

      {/* Modals & Dialogs */}
      <AccountManagerModal
        show={accountsState.showAccountManagerModal}
        onClose={() => accountsState.setShowAccountManagerModal(false)}
        accounts={accountsState.accounts}
        selectedAccount={accountsState.selectedAccount}
        newAccountName={accountsState.newAccountName}
        setNewAccountName={accountsState.setNewAccountName}
        handleCreateAccount={accountsState.handleCreateAccount}
        handleAccountChange={accountsState.handleAccountChange}
        handleTriggerLogin={accountsState.handleTriggerLogin}
        handleOpenTikTokStudioBrowser={accountsState.handleOpenTikTokStudioBrowser}
        handleOpenInstagramBrowser={accountsState.handleOpenInstagramBrowser}
        handleOpenFacebookBrowser={accountsState.handleOpenFacebookBrowser}
        handleLoginInstagramMobile={accountsState.handleLoginInstagramMobile}
        fetchAccounts={accountsState.fetchAccounts}
        loggingInPlatform={accountsState.loggingInPlatform}
        showToast={showToast}
      />

      <AddMediaModal
        show={contentState.showUploadModal}
        onClose={() => contentState.setShowUploadModal(false)}
        selectedAccount={accountsState.selectedAccount}
        availableDates={contentState.availableDates}
        singleMediaFile={contentState.singleMediaFile}
        setSingleMediaFile={contentState.setSingleMediaFile}
        singleMediaPreviewUrl={contentState.singleMediaPreviewUrl}
        setSingleMediaPreviewUrl={contentState.setSingleMediaPreviewUrl}
        carouselSlides={contentState.carouselSlides}
        setCarouselSlides={contentState.setCarouselSlides}
        isScheduledUpload={contentState.isScheduledUpload}
        setIsScheduledUpload={contentState.setIsScheduledUpload}
        uploadScheduleTime={contentState.uploadScheduleTime}
        setUploadScheduleTime={contentState.setUploadScheduleTime}
        uploadDate={contentState.uploadDate}
        setUploadDate={contentState.setUploadDate}
        carouselNameInput={contentState.carouselNameInput}
        setCarouselNameInput={contentState.setCarouselNameInput}
        uploadingFileState={contentState.uploadingFileState}
        handleMediaFileUpload={contentState.handleMediaFileUpload}
      />

      <AddDateModal
        show={contentState.showAddDateModal}
        onClose={() => contentState.setShowAddDateModal(false)}
        selectedAccount={accountsState.selectedAccount}
        newDateInput={contentState.newDateInput}
        setNewDateInput={contentState.setNewDateInput}
        handleCreateDateFolder={contentState.handleCreateDateFolder}
      />

      <SettingsModal
        show={settingsState.showSettingsModal}
        onClose={() => settingsState.setShowSettingsModal(false)}
        llmBaseUrl={settingsState.llmBaseUrl}
        setLlmBaseUrl={settingsState.setLlmBaseUrl}
        llmApiKey={settingsState.llmApiKey}
        setLlmApiKey={settingsState.setLlmApiKey}
        llmModel={settingsState.llmModel}
        setLlmModel={settingsState.setLlmModel}
        savingSettings={settingsState.savingSettings}
        testingLlm={settingsState.testingLlm}
        testResult={settingsState.testResult}
        handleSaveSettings={settingsState.handleSaveSettings}
        handleTestLlmConnection={settingsState.handleTestLlmConnection}
      />

      <DeleteConfirmModal
        show={contentState.showDeleteConfirmModal}
        onClose={() => contentState.setShowDeleteConfirmModal(false)}
        itemToDelete={contentState.itemToDelete}
        isDeleting={contentState.isDeleting}
        handleConfirmDelete={contentState.handleConfirmDelete}
      />
    </div>
  );
}
